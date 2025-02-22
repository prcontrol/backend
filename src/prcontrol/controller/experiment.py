import logging
import sched
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from threading import Thread
from typing import TYPE_CHECKING

from prcontrol.controller.common import LedLane, LedPosition, LedSide
from prcontrol.controller.configuration import (
    EventPair,
    Experiment,
    ExperimentTemplate,
    MeasuredDataAtTimePoint,
)
from prcontrol.controller.measurements import Current

if TYPE_CHECKING:
    from prcontrol.controller.controller import Controller

logger = logging.getLogger(__name__)


class Timer:
    callback: Callable[[], None]
    thread: Thread
    datetime_end: datetime
    time_remaining: timedelta
    paused: bool
    running: bool

    def __init__(
        self,
        callback: Callable[[], None],
    ):
        self.callback = callback
        self.thread = Thread(target=self._check_time)
        self.paused = False
        self.running = False

    def set(self, timespan: timedelta) -> None:
        self.datetime_end = datetime.now() + timespan
        self.paused = False
        self.running = True
        self.thread = Thread(target=self._check_time)
        self.thread.start()

    def pause(self) -> None:
        if self.running and not self.paused:
            self.time_remaining = self.datetime_end - datetime.now()
            self.paused = True

    def resume(self) -> None:
        if self.running and self.paused:
            self.datetime_end = datetime.now() + self.time_remaining
            self.paused = False

    def _check_time(self) -> None:
        while self.running:
            if not self.paused and datetime.now() > self.datetime_end:
                self.callback()
                break
            time.sleep(1)


class MeasurementScheduler:
    callback: Callable[[], None]
    interval: float
    thread: Thread
    running: bool
    scheduler: sched.scheduler

    def __init__(self, callback: Callable[[], None], interval: float):
        self.callback = callback
        self.interval = interval

    def start(self) -> None:
        self.thread = Thread(target=self._measure)
        self.running = True
        self.thread.start()

    def _measure(self) -> None:
        while self.running:
            self.callback()
            time.sleep(self.interval)

    def stop(self) -> None:
        self.running = False


class ExperimentRunner:
    controller: "Controller"

    # State of current Experiment
    state_sample: int
    state_led_front: bool
    state_led_back: bool
    is_running: bool
    needs_sample: bool
    state_paused: bool

    # Timers for current experiment
    _timer_sample: Timer
    _timer_led_front: Timer
    _timer_led_back: Timer
    _scheduler: MeasurementScheduler

    # Data of current experiment
    _template: ExperimentTemplate
    _lab_notebook_entry: str
    _measurements: list[MeasuredDataAtTimePoint]
    _events: list[EventPair]
    _canceled: bool
    _neighbours: list[int]
    _error: bool
    _date: str
    _lane: LedLane
    _uid: int
    _start_time: datetime

    def __init__(self, lane: LedLane, controller: "Controller"):
        self.controller = controller

        # Init Public fields
        self._lane = lane
        self.is_running = False
        self.state_sample = 0
        self.state_led_back = False
        self.state_led_front = False
        self.needs_sample = False
        self.state_paused = True

    # Public routines

    def start_experiment(
        self, template: ExperimentTemplate, uid: int, lab_notebook_entry: str
    ) -> None:
        # Setup state
        self.state_sample = 0
        self.state_led_back = template.led_back is not None
        self.state_led_front = template.led_front is not None
        self.is_running = True
        self.needs_sample = False
        self.state_paused = False

        # Setup data collection
        self._template = template
        self._lab_notebook_entry = lab_notebook_entry
        self._measurements = []
        self._events = []
        self._neighbours = []
        self._canceled = False
        self._error = False
        self._date = datetime.today().strftime("%Y-%m-%d")
        self._uid = uid
        self._start_time = datetime.now()

        # Setup Timers
        self._timer_sample = Timer(self._sample)
        self._timer_led_front = Timer(self._led_front_done)
        self._timer_led_back = Timer(self._led_back_done)
        if len(self._template.time_points_sample_taking) >= 1:
            self._timer_sample.set(
                timedelta(seconds=self._template.time_points_sample_taking[0])
            )
        if self.state_led_front:
            self._timer_led_front.set(
                timedelta(seconds=self._template.led_front_exposure_time)
            )
        if self.state_led_back:
            self._timer_led_back.set(
                timedelta(seconds=self._template.led_back_exposure_time)
            )
        self._scheduler = MeasurementScheduler(
            self._measure, self._template.measurement_interval
        )
        self._scheduler.start()

        # Configure LEDs ... is this mA?
        if self.state_led_front:
            if self._template.led_front is None:
                raise ValueError("Should never get here")
            self.controller.power_box.set_led_max_current(
                LedPosition(self._lane, LedSide.FRONT),
                Current.from_milli_amps(self._template.led_front.max_current),
            )

        if self.state_led_back:
            if self._template.led_back is None:
                raise ValueError("Should never get here")
            self.controller.power_box.set_led_max_current(
                LedPosition(self._lane, LedSide.BACK),
                Current.from_milli_amps(self._template.led_back.max_current),
            )

        # Start Exposure
        if self.state_led_front:
            logger.debug("STARTING LED FRONT")
            self.controller.power_box.activate_led(
                LedPosition(self._lane, LedSide.FRONT),
                self._template.led_back_intensity,
            )
        if self.state_led_back:
            logger.debug("STARTING LED BACK")
            self.controller.power_box.activate_led(
                LedPosition(self._lane, LedSide.BACK),
                self._template.led_back_intensity,
            )

        # Register Start
        self.add_event("experiment was started")

    def pause_experiment(self) -> None:
        if self.is_running and not self.state_paused:
            self.state_paused = True
            self.add_event("experiment was paused")
            self._timer_sample.pause()
            self._timer_led_back.pause()
            self._timer_led_front.pause()
            if self.state_led_front:
                self.controller.power_box.deactivate_led(
                    LedPosition(self._lane, LedSide.FRONT)
                )
            if self.state_led_back:
                self.controller.power_box.deactivate_led(
                    LedPosition(self._lane, LedSide.BACK)
                )

    def resume_experiment(self) -> None:
        if self.is_running and self.state_paused and not self.needs_sample:
            self.state_paused = False
            self.add_event("experiment was resumed")
            self._timer_sample.resume()
            self._timer_led_back.resume()
            self._timer_led_front.resume()
            if self.state_led_front:
                self.controller.power_box.activate_led(
                    LedPosition(self._lane, LedSide.FRONT),
                    self._template.led_back_intensity,
                )
            if self.state_led_back:
                self.controller.power_box.activate_led(
                    LedPosition(self._lane, LedSide.BACK),
                    self._template.led_back_intensity,
                )

    def sample_was_taken(self) -> None:
        if self.is_running and self.needs_sample:
            self.add_event("sample was taken")
            self.needs_sample = False
            if (
                self.state_sample
                == len(self._template.time_points_sample_taking)
                and not self.state_led_back
                and not self.state_led_front
            ):
                self._finish_experiment()
            elif self.state_sample < len(
                self._template.time_points_sample_taking
            ):
                timestamp = self._template.time_points_sample_taking[
                    self.state_sample
                ]
                self._timer_sample = Timer(self._sample)
                self._timer_sample.set(timedelta(seconds=timestamp))
                self.resume_experiment()
            else:
                self.resume_experiment()

    def add_event(self, event: str) -> None:
        logger.debug(f"Received event {event}")
        if self.is_running:
            time = (datetime.now() - self._start_time).total_seconds()
            self._events.append(EventPair(time, event))

    def cancel(self) -> None:
        if self.is_running:
            self.is_running = False
            self.add_event("experiment was cancelled")
            self._canceled = True
            self.controller.power_box.deactivate_led(
                LedPosition(self._lane, LedSide.FRONT)
            )
            self.controller.power_box.deactivate_led(
                LedPosition(self._lane, LedSide.BACK)
            )
            self._finish_experiment()

    def registerNeighbourExperiment(self, uid: int) -> None:
        if self.is_running:
            self.add_event("neighbour experiment started: " + str(uid))
            self._neighbours.append(uid)

    def register_error(self) -> None:
        if self.is_running:
            self._error = True

    def has_uv(self) -> bool:
        if self.state_led_front:
            if self._template.led_front is None:
                raise ValueError("Should never get here")
            if self._template.led_front.is_uv():
                return True
        if self.state_led_back:
            if self._template.led_back is None:
                raise ValueError("Should never get here")
            if self._template.led_back.is_uv():
                return True
        return False

    # Private Routines

    def _finish_experiment(self) -> None:
        self.add_event("experiment was finished")
        self.is_running = False
        self._scheduler.stop()
        template = self._template
        data = Experiment(
            uid=self._uid,
            name=template.name,
            lab_notebook_entry=self._lab_notebook_entry,
            date=self._date,
            config_file=template.config_file,
            template_uid=self._template.get_uid(),
            active_lane=self._lane.demux(1, 2, 3),
            led_front=template.led_front,
            led_front_intensity=template.led_front_intensity,
            led_front_distance_to_vial=template.led_front_distance_to_vial,
            led_front_exposure_time=template.led_front_exposure_time,
            led_back=template.led_back,
            led_back_intensity=template.led_back_intensity,
            led_back_distance_to_vial=template.led_back_distance_to_vial,
            led_back_exposure_time=template.led_back_exposure_time,
            time_points_sample_taking=template.time_points_sample_taking,
            size_sample=self._template.size_sample,
            parallel_experiments=tuple(self._neighbours),
            position_thermocouple=template.position_thermocouple,
            error_occured=self._error,
            experiment_cancelled=self._canceled,
            event_log=tuple(self._events),
            measured_data=tuple(self._measurements),
        )
        self.controller.end_experiment(self._lane, data)

    # Callbacks from timer

    def _sample(self) -> None:
        if self.is_running:
            self.add_event("need to take sample")
            self.needs_sample = True
            self.state_sample += 1
            self.pause_experiment()
            self.controller.alert_take_sample(self._lane)

    def _led_front_done(self) -> None:
        if self.is_running:
            self.controller.power_box.deactivate_led(
                LedPosition(self._lane, LedSide.FRONT)
            )
            self.state_led_front = False
            if not self.state_led_back and self.state_sample == len(
                self._template.time_points_sample_taking
            ):
                self._finish_experiment()

    def _led_back_done(self) -> None:
        if self.is_running:
            self.controller.power_box.deactivate_led(
                LedPosition(self._lane, LedSide.BACK)
            )
            self.state_led_back = False
            if not self.state_led_front and self.state_sample == len(
                self._template.time_points_sample_taking
            ):
                self._finish_experiment()

    def _measure(self) -> None:
        if not self.is_running:
            return

        data = self.controller.state
        time = (datetime.now() - self._start_time).total_seconds()

        pst = data.power_box_state
        rst = data.reactor_box_state

        measured_data = MeasuredDataAtTimePoint(
            timepoint=time,
            temperature_thermocouple=rst.thermocouble_temp.celsius,
            ambient_temp_strombox=pst.abmient_temperature.celsius,
            ambient_temp_photobox=rst.ambient_temperature.celsius,
            voltage_lane1=average(
                pst.voltage_lane_1_back.milli_volts,
                pst.voltage_lane_1_front.milli_volts,
            ),
            voltage_lane2=average(
                pst.voltage_lane_2_back.milli_volts,
                pst.voltage_lane_2_front.milli_volts,
            ),
            voltage_lane3=average(
                pst.voltage_lane_3_back.milli_volts,
                pst.voltage_lane_3_front.milli_volts,
            ),
            current_lane1=average(
                pst.current_lane_1_back.milli_amps,
                pst.current_lane_1_front.milli_amps,
            ),
            current_lane2=average(
                pst.current_lane_2_back.milli_amps,
                pst.current_lane_2_front.milli_amps,
            ),
            current_lane3=average(
                pst.current_lane_3_back.milli_amps,
                pst.current_lane_3_front.milli_amps,
            ),
            ir_temp_lane1=rst.lane_1_ir_temp.celsius,
            ir_temp_lane2=rst.lane_2_ir_temp.celsius,
            ir_temp_lane3=rst.lane_3_ir_temp.celsius,
            uv_index=rst.uv_index.uvi,
            ambient_light=rst.ambient_light.hudreth_lux,
        )
        self._measurements.append(measured_data)


class ExperimentSupervisor:
    runners: list[ExperimentRunner]
    controller: "Controller"

    # Auto Pause Feature
    auto_paused: set[LedLane]
    sample_was_taken_during_open: set[LedLane]
    box_open: bool

    def __init__(self, controller: "Controller"):
        self.runners = []
        self.runners.append(ExperimentRunner(LedLane.LANE_1, controller))
        self.runners.append(ExperimentRunner(LedLane.LANE_2, controller))
        self.runners.append(ExperimentRunner(LedLane.LANE_3, controller))
        self.controller = controller
        self.auto_paused = set()
        self.sample_was_taken_during_open = set()
        self.box_open = False

    # Public Methods for "Controller"

    def is_running(self) -> bool:
        return all(runner.is_running for runner in self.runners)

    def start_experiment_on(
        self,
        lane: LedLane,
        template: ExperimentTemplate,
        uid: int,
        lab_notebook_entry: str,
    ) -> None:
        logger.info(
            f"Stating experiment on lane {lane}"
            f" using template {template.get_uid()}"
        )
        self.runners[lane.demux(0, 1, 2)] = ExperimentRunner(
            lane, self.controller
        )
        self.runners[lane.demux(0, 1, 2)].start_experiment(
            template, uid, lab_notebook_entry
        )
        for r in self.runners:
            if r._lane != lane:
                r.registerNeighbourExperiment(uid)

        self.controller.state.uv_installed = any(
            runners.has_uv() for runners in self.runners
        )

    def pause_experiment_on(self, lane: LedLane) -> None:
        if not self.box_open:
            logger.debug(f"Pausing on lane {lane}.")
            self.runners[lane.demux(0, 1, 2)].pause_experiment()
        else:
            self.auto_paused.discard(lane)

    def resume_experiment_on(self, lane: LedLane) -> None:
        if not self.box_open:
            logger.debug(f"Resuming on lane {lane}.")
            self.runners[lane.demux(0, 1, 2)].resume_experiment()
        else:
            self.auto_paused.add(lane)

    def cancel_experiment_on(self, lane: LedLane) -> None:
        logger.debug(f"Canceling on lane {lane}.")
        self.runners[lane.demux(0, 1, 2)].cancel()

    def sample_was_taken_on(self, lane: LedLane) -> None:
        if not self.box_open:
            logger.debug(f"Sample taken on lane {lane}.")
            self.runners[lane.demux(0, 1, 2)].sample_was_taken()
        else:
            self.sample_was_taken_during_open.add(lane)

    def add_event_on(self, lane: LedLane, event: str) -> None:
        logger.debug(f"Event {event} on lane {lane}.")
        self.runners[lane.demux(0, 1, 2)].add_event(event)

    def register_error_on(self, lane: LedLane) -> None:
        logger.warning(f"Registered error on lane {lane}")
        self.runners[lane.demux(0, 1, 2)].register_error()

    def auto_pause_on_open_box(self) -> None:
        self.box_open = True
        for runner in self.runners:
            if runner.is_running and not runner.state_paused:
                self.auto_paused.add(runner._lane)
                runner.pause_experiment()

    def auto_resume_on_closed_box(self) -> None:
        self.box_open = False
        auto_paused = self.auto_paused.copy()
        for lane in auto_paused:
            self.auto_paused.remove(lane)
            self.resume_experiment_on(lane)
        sample_was_taken_during_open = self.sample_was_taken_during_open.copy()
        for lane in sample_was_taken_during_open:
            self.sample_was_taken_during_open.remove(lane)
            self.sample_was_taken_on(lane)


def average(*data: int | float) -> float:
    return sum(data) / len(data)
