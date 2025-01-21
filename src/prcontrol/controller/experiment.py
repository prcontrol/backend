from datetime import datetime, timedelta  # noqa: F401
from threading import Thread, Timer
from typing import Callable  # noqa: UP035

from prcontrol.controller.common import LedLane
from prcontrol.controller.configuration import Experiment, ExperimentTemplate
from prcontrol.controller.controller import Controller


class Timer:  # noqa: F811
    callback_sample: Callable[[None], None]
    callback_led_front: Callable[[None], None]
    callback_led_back: Callable[[None], None]
    callback_measure: Callable[[None], None]
    measure_intervall: float
    thread: Thread

    def __init__(
        self,
        callback_sample: Callable[[None], None],
        callback_led_front: Callable[[None], None],
        callback_led_back: Callable[[None], None],
        callback_measure: Callable[[None], None],
        measure_intervall: float,
    ):  # noqa: E501
        self.callback_sample = callback_sample
        self.callback_led_front = callback_led_front
        self.callback_led_back = callback_led_back
        self.callback_measure = callback_measure
        self.measure_intervall = measure_intervall

    def next_sample_in(timespan: float):
        raise NotImplementedError()

    def led_front_time(timespan: float):
        raise NotImplementedError()

    def led_back_time(timespan: float):
        raise NotImplementedError()

    def pause():
        raise NotImplementedError()

    def resume():
        raise NotImplementedError()

    def reset():
        raise NotImplementedError()


class ExperimentSupervisor:
    controller: Controller

    # Lane1
    timer_1: Timer
    template_1: ExperimentTemplate

    state_sample_1: int
    state_led_front_1: bool
    state_led_back_1: bool

    data_1: Experiment
    endExperiment_on_1: Callable[[Experiment], None]

    # Lane2
    timer_2: Timer
    template_2: ExperimentTemplate

    state_sample_2: int
    state_led_front_2: bool
    state_led_back_2: bool

    data_2: Experiment
    endExperiment_on_2: Callable[[Experiment], None]

    # Lane3
    timer_3: Timer
    template_3: ExperimentTemplate

    state_sample_3: int
    state_led_front_3: bool
    state_led_back_3: bool

    data_3: Experiment
    endExperiment_on_3: Callable[[Experiment], None]

    def __init__(self):
        timer_1 = Timer(  # noqa: F841
            self._sample_on_lane_1,
            self._led_front_done_1,
            self._led_back_done_1,
            self._measure_on_lane_1,
            1.0,
        )  # noqa: E501, F841
        timer_2 = Timer(  # noqa: F841
            self._sample_on_lane_2,
            self._led_front_done_2,
            self._led_back_done_2,
            self._measure_on_lane_2,
            1.0,
        )  # noqa: E501, F841
        timer_3 = Timer(  # noqa: F841
            self._sample_on_lane_3,
            self._led_front_done_3,
            self._led_back_done_3,
            self._measure_on_lane_1,
            1.0,
        )  # noqa: E501, F841

    def start_experiment(self, lane: LedLane, template: ExperimentTemplate):
        raise NotImplementedError()

    def pause_experiment(self, lane: LedLane):
        raise NotImplementedError()

    def resume_experiment(self, lane: LedLane):
        raise NotImplementedError()

    # Private Routines

    def finish_experiment_on(lane: LedLane):
        raise NotImplementedError

    # Callbacks Lane 1

    def _sample_on_lane_1():
        raise NotImplementedError()

    def _led_front_done_1():
        raise NotImplementedError

    def _led_back_done_1():
        raise NotImplementedError

    def _measure_on_lane_1():
        raise NotImplementedError()

    # Callbacks Lane 2

    def _sample_on_lane_2():
        raise NotImplementedError()

    def _led_front_done_2():
        raise NotImplementedError

    def _led_back_done_2():
        raise NotImplementedError

    def _measure_on_lane_2():
        raise NotImplementedError()

    # Callbacks Lane 3

    def _sample_on_lane_3():
        raise NotImplementedError()

    def _led_front_done_3():
        raise NotImplementedError

    def _led_back_done_3():
        raise NotImplementedError

    def _measure_on_lane_3():
        raise NotImplementedError()
