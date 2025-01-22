import time
from datetime import datetime, timedelta  # noqa: F401
from threading import Thread
from typing import Callable  # noqa: UP035

import attrs

from prcontrol.controller.common import LedLane, LedState
from prcontrol.controller.configuration import (
    EventPair,
    Experiment,
    ExperimentTemplate,
    JSONSeriablizable,
    MeasuredDataAtTimePoint,
)


class Timer:  # noqa: F811
    callback_sample: Callable[[None], None]
    callback_led_front: Callable[[None], None]
    callback_led_back: Callable[[None], None]
    callback_measure: Callable[[None], None]
    measure_interval: float

    thread: Thread

    datetime_start: datetime

    datetime_led_front: datetime
    datetime_led_back: datetime
    datetime_next_sample: datetime

    time_led_front_set: bool
    time_led_back_set: bool
    time_next_sample_set: bool

    time_remaining_led_front: timedelta
    time_remaining_led_back: timedelta
    time_remaining_next_sample: timedelta

    running: bool
    paused: bool

    def __init__(
        self,
        callback_sample: Callable[[None], None],
        callback_led_front: Callable[[None], None],
        callback_led_back: Callable[[None], None],
        callback_measure: Callable[[None], None],
        measure_interval: float,
    ):  # noqa: E501
        self.callback_sample = callback_sample
        self.callback_led_front = callback_led_front
        self.callback_led_back = callback_led_back
        self.callback_measure = callback_measure
        self.measure_interval = measure_interval

        self.datetime_start = datetime.now()

        self.datetime_led_front = datetime.now()
        self.datetime_led_back = datetime.now()
        self.datetime_next_sample = datetime.now()

        self.time_led_front_set = False
        self.time_led_back_set = False
        self.time_next_sample_set = False

        self.thread = Thread(target=self._check_time)

    def next_sample_in(self, timespan: float):
        current_time = datetime.now()
        delta = datetime.timedelta(seconds=timespan)
        self.datetime_next_sample = current_time + delta
        self.time_led_front_set = True

    def led_front_time(self, timespan: float):
        current_time = datetime.now()
        delta = datetime.timedelta(seconds=timespan)
        self.datetime_led_front = current_time + delta
        self.time_led_front_set = True

    def led_back_time(self, timespan: float):
        current_time = datetime.now()
        delta = datetime.timedelta(seconds=timespan)
        self.datetime_led_back = current_time + delta
        self.time_led_back_set = True

    def start(self):
        self.datetime_start = datetime.now()
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        # self.thread.join() # TODO is probably called within the same thread

    def time_since_start(self) -> float:
        current_time = datetime.now()
        delta = current_time - self.datetime_start
        return delta.total_seconds()

    def pause(self):
        current_time = datetime.now()
        self.time_remaining_led_front = self.datetime_led_front - current_time
        self.time_remaining_led_back = self.datetime_led_back - current_time
        self.time_remaining_next_sample = (
            self.datetime_next_sample - current_time
        )

        self.paused = True

    def resume(self):
        current_time = datetime.now()
        self.datetime_led_front = current_time + self.time_remaining_led_front
        self.datetime_led_back = current_time + self.time_remaining_led_back
        self.datetime_next_sample = (
            current_time + self.time_remaining_next_sample
        )

        self.paused = False

    def reset(self):
        self.time_led_front_set = False
        self.time_led_back_set = False
        self.time_next_sample_set = False

    def _check_time(self):
        while self.running:
            if not self.paused:
                self.callback_measure()
                current_time = datetime.now()
                if (
                    self.time_next_sample_set
                    and current_time > self.datetime_next_sample
                ):
                    self.time_next_sample_set = False
                    self.callback_sample()
                if (
                    self.time_led_front_set
                    and current_time > self.datetime_led_front
                ):
                    self.time_led_front_set = False
                    self.callback_led_front()
                if (
                    self.time_led_back_set
                    and current_time > self.datetime_led_back
                ):
                    self.time_led_back_set = False
                    self.callback_led_back()
            time.sleep(1)


@attrs.frozen(slots=True)
class MeasuredData(JSONSeriablizable):
    temperature_thermocouple: float
    ambient_temp_strombox: float
    ambient_temp_photobox: float
    voltage_lane1: float
    current_lane1: float
    ir_temp_lane1: float
    voltage_lane2: float
    current_lane2: float
    ir_temp_lane2: float
    voltage_lane3: float
    current_lane3: float
    ir_temp_lane3: float
    uv_index: float
    ambient_light: float


class ExperimentRunner:
    timer: Timer
    template: ExperimentTemplate  # Nullable

    state_sample: int
    state_led_front: bool
    state_led_back: bool
    is_running: bool
    needs_sample: bool

    _measurements: list[MeasuredDataAtTimePoint]
    _events: list[EventPair]
    _canceled: bool
    _neighbours: list[int]
    _error: bool
    _date: str
    _lane: LedLane
    _uid: int

    set_intensity_front: Callable[[int], None]
    set_intensity_back: Callable[[int], None]
    end_experiment: Callable[[Experiment], None]
    update_led_front: Callable[[LedState], None]
    update_led_back: Callable[[LedState], None]
    measure: Callable[[None], MeasuredData]
    take_sample: Callable[[None], None]

    def __init__(
        self,
        lane: LedLane,
        measureIntervall: int,
        set_intensity_front: Callable[[int], None],
        set_intensity_back: Callable[[int], None],
        end_experiment: Callable[[Experiment], None],
        update_led_front: Callable[[LedState], None],
        update_led_back: Callable[[LedState], None],
        measure: Callable[[None], MeasuredData],
        take_sample: Callable[[None], None],
    ):
        self.timer = Timer(
            self._sample,
            self._led_front,
            self._led_back,
            self._measure,
            measureIntervall,
        )
        self.is_running = False
        self.state_sample = 0
        self.state_led_back = False
        self.state_led_front = False
        self.needs_sample = False
        self._measurements = []
        self._events = []
        self._neighbours = []
        self._canceled = False
        self._error = False
        self._date = ""
        self._lane = lane
        self._uid = 0
        self.set_intensity_front = set_intensity_front
        self.set_intensity_back = set_intensity_back
        self.end_experiment = end_experiment
        self.update_led_front = update_led_front
        self.update_led_back = update_led_back
        self.measure = measure
        self.take_sample = take_sample

    # Public routines

    def start_experiment(self, template: ExperimentTemplate, uid: int):
        # Setup state
        self.state_sample = 0
        self.state_led_back = True
        self.state_led_front = True
        self.is_running = True
        self.needs_sample = False

        # Setup data collection
        self.template = template
        self._measurements = []
        self._events = []
        self._neighbours = []
        self._canceled = False
        self._error = False
        self._date = datetime.today().strftime("%Y-%m-%d")
        self._uid = uid

        # Setup Timer
        self.timer.reset()
        self.timer.led_back_time(self.template.led_back_exposure_time)
        self.timer.led_front_time(self.template.led_front_exposure_time)
        self.timer.next_sample_in(self.template.time_points_sample_taking[0])
        self.timer.start()

        # Start Exposure
        self.set_intensity_back(self.template.led_back_intensity)
        self.set_intensity_front(self.template.led_front_intensity)
        self.update_led_back(LedState.HIGH)
        self.update_led_front(LedState.HIGH)

    def pause_experiment(self):
        assert self.is_running
        self.timer.pause()
        self.update_led_back(LedState.LOW)
        self.update_led_front(LedState.LOW)

    def resume_experiment(self):
        assert self.is_running
        self.timer.resume()
        self.update_led_back(LedState.HIGH)
        self.update_led_front(LedState.HIGH)

    def sample_was_taken(self):
        assert self.is_running
        assert self.needs_sample
        self.needs_sample = False
        timestamp = (
            self.template.time_points_sample_taking[self.state_sample]
            - self.template.time_points_sample_taking[self.state_sample - 1]
        )
        self.timer.next_sample_in(timestamp)
        self.resume_experiment()

    def add_event(self, event: str):
        assert self.is_running
        time = self.timer.time_since_start()
        self._events.append(EventPair(time, event))

    def cancel(self):
        assert self.is_running
        self._canceled = True
        self.update_led_back(LedState.LOW)
        self.update_led_front(LedState.LOW)
        self._finish_experiment()

    def registerNeighbourExperiment(self, uid: int):
        assert self.is_running
        self._neighbours.append(uid)

    def register_error(self):
        assert self.is_running
        self._error = True

    # Private Routines

    def _finish_experiment(self):
        self.is_running = False
        self.timer.stop()
        data = Experiment(
            uid=self._uid,
            name=self.template.name,
            lab_notebook_entry="",  # Frontend
            date=self.date,
            config_file=self.template.config_file,
            active_lane=self._lane.demux(1, 2, 3),
            led_front=self.template.led_front,
            led_front_intensity=self.template.led_front_intensity,
            led_front_distance_to_vial=self.template.led_front_distance_to_vial,
            led_front_exposure_time=self.template.led_front_exposure_time,
            led_back=self.template.led_back,
            led_back_intensity=self.template.led_back_intensity,
            led_back_distance_to_vial=self.template.led_back_distance_to_vial,
            led_back_exposure_time=self.template.led_back_exposure_time,
            time_points_sample_taking=self.template.time_points_sample_taking,
            size_sample=0.0,  # Frontend
            parallel_experiments=tuple(self._neighbours),
            position_thermocouple=self.template.position_thermocouple,
            error_occured=self._error,
            experiment_cancelled=self._canceled,
            event_log=tuple(self._events),
            measured_data=tuple(self._measurements),
        )
        self.end_experiment(data)

    # Callbacks from timer

    def _sample(self):
        self.needs_sample = True
        self.pause_experiment()
        self.take_sample()
        self.state_sample += 1
        if (
            self.state_sample == len(self.template.time_points_sample_taking)
            and not self.state_led_back
            and not self.state_led_front
        ):
            self._finish_experiment()

    def _led_front_done(self):
        self.update_led_front(LedState.LOW)
        self.state_led_front = False
        if not self.state_led_back and self.state_sample == len(
            self.template.time_points_sample_taking
        ):
            self._finish_experiment()

    def _led_back_done(self):
        self.update_led_back(LedState.LOW)
        self.state_led_back = False
        if not self.state_led_front and self.state_sample == len(
            self.template.time_points_sample_taking
        ):
            self._finish_experiment()

    def _measure(self):
        data = self.measure()
        time = self.timer.time_since_start()
        self._measurements.append(
            MeasuredDataAtTimePoint(
                timepoint=time,
                temperature_thermocouple=data.temperature_thermocouple,
                ambient_temp_strombox=data.ambient_temp_strombox,
                ambient_temp_photobox=data.ambient_temp_photobox,
                voltage_lane1=data.voltage_lane1,
                voltage_lane2=data.voltage_lane2,
                voltage_lane3=data.voltage_lane3,
                current_lane1=data.current_lane1,
                current_lane2=data.current_lane2,
                current_lane3=data.current_lane3,
                ir_temp_lane1=data.ir_temp_lane1,
                ir_temp_lane2=data.ir_temp_lane2,
                ir_temp_lane3=data.ir_temp_lane3,
                uv_index=data.uv_index,
                ambient_light=data.ambient_light,
            )
        )


class ExperimentSupervisor:
    runner_1: ExperimentRunner
    runner_2: ExperimentRunner
    runner_3: ExperimentRunner

    # Callbacks for Controller
    measure: Callable[[None], MeasuredData]
    set_intensity_front: Callable[[LedLane, int], None]
    set_intensity_back: Callable[[LedLane, int], None]
    update_led_front: Callable[[LedLane, LedState], None]
    update_led_back: Callable[[LedLane, LedState], None]
    end_experiment: Callable[[LedLane, Experiment], None]
    take_sample: Callable[[LedLane, None], None]

    def __init__(
        self,
        measure: Callable[[None], MeasuredData],
        set_intensity_front: Callable[[LedLane, int], None],
        set_intensity_back: Callable[[LedLane, int], None],
        update_led_front: Callable[[LedLane, LedState], None],
        update_led_back: Callable[[LedLane, LedState], None],
        end_experiment: Callable[[LedLane, Experiment], None],
        take_sample: Callable[[LedLane, None], None],
    ):
        self.measure = measure
        self.set_intensity_back = set_intensity_back
        self.set_intensity_front = set_intensity_front
        self.update_led_back = update_led_back
        self.update_led_front = update_led_front
        self.take_sample = take_sample
        self.end_experiment = end_experiment
        self.runner_1 = ExperimentRunner(
            lane=LedLane.LANE_1,
            measureIntervall=1,
            set_intensity_front=self._set_intensity_front_1,
            set_intensity_back=self._set_intensity_back_1,
            end_experiment=self._end_experiment_1,
            update_led_front=self._update_led_front_1,
            update_led_back=self._update_led_back_1,
            measure=self.measure,
            take_sample=self._take_sample_1,
        )
        self.runner_2 = ExperimentRunner(
            lane=LedLane.LANE_2,
            measureIntervall=1,
            set_intensity_front=self._set_intensity_front_2,
            set_intensity_back=self._set_intensity_back_2,
            end_experiment=self._end_experiment_2,
            update_led_front=self._update_led_front_2,
            update_led_back=self._update_led_back_2,
            measure=self.measure,
            take_sample=self._take_sample_2,
        )
        self.runner_3 = ExperimentRunner(
            lane=LedLane.LANE_3,
            measureIntervall=1,
            set_intensity_front=self._set_intensity_front_3,
            set_intensity_back=self._set_intensity_back_3,
            end_experiment=self._end_experiment_3,
            update_led_front=self._update_led_front_3,
            update_led_back=self._update_led_back_3,
            measure=self.measure,
            take_sample=self._take_sample_3,
        )

    # Public Methods for Controller

    def start_experiment_on(
        self, lane: LedLane, template: ExperimentTemplate, uid: int
    ):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.start_experiment(template, uid)
            case LedLane.LANE_2:
                self.runner_2.start_experiment(template, uid)
            case LedLane.LANE_3:
                self.runner_3.start_experiment(template, uid)

        if self.runner_1.is_running:
            self.runner_1.registerNeighbourExperiment(uid)
        if self.runner_2.is_running:
            self.runner_2.registerNeighbourExperiment(uid)
        if self.runner_3.is_running:
            self.runner_3.registerNeighbourExperiment(uid)

    def pause_experiment_on(self, lane: LedLane):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.pause_experiment()
            case LedLane.LANE_2:
                self.runner_2.pause_experiment()
            case LedLane.LANE_3:
                self.runner_3.pause_experiment()

    def resume_experiment_on(self, lane: LedLane):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.resume_experiment()
            case LedLane.LANE_2:
                self.runner_2.resume_experiment()
            case LedLane.LANE_3:
                self.runner_3.resume_experiment()

    def cancel_experiment_on(self, lane: LedLane):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.cancel()
            case LedLane.LANE_2:
                self.runner_2.cancel()
            case LedLane.LANE_3:
                self.runner_3.cancel()

    def sample_was_taken_on(self, lane: LedLane):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.sample_was_taken()
            case LedLane.LANE_2:
                self.runner_2.sample_was_taken()
            case LedLane.LANE_3:
                self.runner_3.sample_was_taken()

    def add_event_on(self, lane: LedLane, event: str):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.add_event(event)
            case LedLane.LANE_2:
                self.runner_2.add_event(event)
            case LedLane.LANE_3:
                self.runner_3.add_event(event)

    def register_error_on(self, lane: LedLane):
        match lane:
            case LedLane.LANE_1:
                self.runner_1.register_error()
            case LedLane.LANE_2:
                self.runner_2.register_error()
            case LedLane.LANE_3:
                self.runner_3.register_error()

    # Route Callbacks from runners
    # Lane 1

    def _set_intensity_front_1(self, intensity: int):
        self.set_intensity_front(LedLane.LANE_1, intensity)

    def _set_intensity_back_1(self, intensity: int):
        self.set_intensity_back(LedLane.LANE_1, intensity)

    def _update_led_front_1(self, new_state: LedState):
        self.update_led_front(LedLane.LANE_1, new_state)

    def _update_led_back_1(self, new_state: LedState):
        self.update_led_back(LedLane.LANE_1, new_state)

    def _take_sample_1(self):
        self.take_sample(LedLane.LANE_1)

    def _end_experiment_1(self, data: Experiment):
        self.end_experiment(LedLane.LANE_1, data)

    # Lane 2

    def _set_intensity_front_2(self, intensity: int):
        self.set_intensity_front(LedLane.LANE_2, intensity)

    def _set_intensity_back_2(self, intensity: int):
        self.set_intensity_back(LedLane.LANE_2, intensity)

    def _update_led_front_2(self, new_state: LedState):
        self.update_led_front(LedLane.LANE_2, new_state)

    def _update_led_back_2(self, new_state: LedState):
        self.update_led_back(LedLane.LANE_2, new_state)

    def _take_sample_2(self):
        self.take_sample(LedLane.LANE_2)

    def _end_experiment_2(self, data: Experiment):
        self.end_experiment(LedLane.LANE_2, data)

    # Lane 3

    def _set_intensity_front_3(self, intensity: int):
        self.set_intensity_front(LedLane.LANE_3, intensity)

    def _set_intensity_back_3(self, intensity: int):
        self.set_intensity_back(LedLane.LANE_3, intensity)

    def _update_led_front_3(self, new_state: LedState):
        self.update_led_front(LedLane.LANE_3, new_state)

    def _update_led_back_3(self, new_state: LedState):
        self.update_led_back(LedLane.LANE_3, new_state)

    def _take_sample_3(self):
        self.take_sample(LedLane.LANE_3)

    def _end_experiment_3(self, data: Experiment):
        self.end_experiment(LedLane.LANE_3, data)
