import time
from datetime import datetime
from typing import Self

from prcontrol.controller.common import LedLane, LedPosition, LedSide
from prcontrol.controller.configuration import (
    LED,
    EventPair,
    Experiment,
    ExperimentTemplate,
    HardwareConfig,
)
from prcontrol.controller.controller import ControllerState
from prcontrol.controller.experiment import ExperimentSupervisor
from prcontrol.controller.measurements import Current
from prcontrol.controller.power_box import PowerBoxSensorState
from prcontrol.controller.reactor_box import ReactorBoxSensorState


class ExperimentLogger:
    done: dict[LedLane, bool]
    times_samples: dict[LedLane, int]
    times_activation_led: dict[LedLane, int]
    times_deactivation_led: dict[LedLane, int]
    log: list[EventPair]
    exp_data: dict[LedLane, Experiment]

    def __init__(self):
        self.done = {}
        self.done[LedLane.LANE_1] = False
        self.done[LedLane.LANE_2] = False
        self.done[LedLane.LANE_3] = False
        self.times_samples = {}
        self.times_samples[LedLane.LANE_1] = 0
        self.times_samples[LedLane.LANE_2] = 0
        self.times_samples[LedLane.LANE_3] = 0
        self.times_activation_led = {}
        self.times_activation_led[LedLane.LANE_1] = 0
        self.times_activation_led[LedLane.LANE_2] = 0
        self.times_activation_led[LedLane.LANE_3] = 0
        self.times_deactivation_led = {}
        self.times_deactivation_led[LedLane.LANE_1] = 0
        self.times_deactivation_led[LedLane.LANE_2] = 0
        self.times_deactivation_led[LedLane.LANE_3] = 0
        self.log = []
        self.start_time = datetime.now()
        self.exp_data = {}

    def register_sample(self, lane: LedLane):
        self.times_samples[lane] += 1
        timepoint = (datetime.now() - self.start_time).total_seconds()
        self.log.append(EventPair(timepoint, "[take sample]"))

    def register_done(self, lane: LedLane, data: Experiment):
        self.done[lane] = True
        self.exp_data[lane] = data
        timepoint = (datetime.now() - self.start_time).total_seconds()
        self.log.append(EventPair(timepoint, "[done]"))

    def register_activate_led(self, lane: LedLane):
        self.times_activation_led[lane] += 1
        timepoint = (datetime.now() - self.start_time).total_seconds()
        self.log.append(EventPair(timepoint, "[activate LED]"))

    def register_deactivate_led(self, lane: LedLane):
        self.times_deactivation_led[lane] += 1
        timepoint = (datetime.now() - self.start_time).total_seconds()
        self.log.append(EventPair(timepoint, "[deactivate LED]"))


class MockPowerbox:
    led: dict[LedPosition, bool]
    logger: ExperimentLogger

    def __init__(self, logger: ExperimentLogger):
        self.logger = logger
        self.led = {}
        self.led[LedPosition(LedLane.LANE_1, LedSide.FRONT)] = False
        self.led[LedPosition(LedLane.LANE_1, LedSide.BACK)] = False
        self.led[LedPosition(LedLane.LANE_2, LedSide.FRONT)] = False
        self.led[LedPosition(LedLane.LANE_2, LedSide.BACK)] = False
        self.led[LedPosition(LedLane.LANE_3, LedSide.FRONT)] = False
        self.led[LedPosition(LedLane.LANE_3, LedSide.BACK)] = False

    def set_led_max_current(self, led: LedPosition, current: Current) -> Self:
        # TODO ExperminetLogger
        return self

    def activate_led(
        self, position: LedPosition, target_intensity: float
    ) -> Self:
        assert not self.led[position]
        self.led[position] = True
        self.logger.register_activate_led(position.lane)
        return self

    def deactivate_led(self, position: LedPosition) -> Self:
        assert self.led[position]
        self.led[position] = False
        self.logger.register_deactivate_led(position.lane)
        return self


class MockController:
    power_box: MockPowerbox
    state: ControllerState
    logger: ExperimentLogger
    supervisor: "ExperimentSupervisor"
    done: bool

    def __init__(self, logger: ExperimentLogger):
        self.supervisor = ExperimentSupervisor(self)
        self.power_box = MockPowerbox(logger)
        self.state = ControllerState.default(
            ReactorBoxSensorState.empty(), PowerBoxSensorState.empty()
        )
        self.logger = logger
        self.done = False

    def end_experiment(self, lane: LedLane, data: Experiment) -> None:
        assert not self.done  # Only end once
        self.done = True
        self.logger.register_done(lane, data)

    def alert_take_sample(self, lane: LedLane) -> Self:
        self.logger.register_sample(lane)
        self.supervisor.sample_was_taken_on(lane)
        return self


def get_template_with(
    duration_front: float,
    duration_back: float,
    samples: tuple[float, ...],
    measurement_interval: float,
) -> ExperimentTemplate:
    return ExperimentTemplate(
        uid=1,
        name="Name",
        date="Today",
        config_file=HardwareConfig(
            uid=1,
            name="Name",
            tinkerforge_bricklets=(),
            software_version="",
            date="",
            default_distance_led_vial=1.0,
            default_position_thermocouple="",
            default_pwm_channels=(),
            default_temperature_threshold=20.0,
            default_uv_threshold=1.0,
            default_sensor_query_interval=1.0,
            default_reaction_vessel_volume=1.0,
        ),
        active_lane=1,
        led_front=LED(
            uid=1,
            name="Name",
            fwhm=1,
            max_of_emission=1,
            min_wavelength=1,
            max_wavelength=1,
            color="",
            max_current=1,
            manufacturer_id=1,
            order_id=1,
            date_soldering="",
            soldered_by="",
            operating_time=1.0,
            defect=False,
            emission_spectrum=(),
            emission_spectrum_recorded_on="",
        ),
        led_front_intensity=1,
        led_front_distance_to_vial=1.0,
        led_front_exposure_time=duration_front,
        led_back=LED(
            uid=2,
            name="Name",
            fwhm=1,
            max_of_emission=1,
            min_wavelength=1,
            max_wavelength=1,
            color="",
            max_current=1,
            manufacturer_id=1,
            order_id=1,
            date_soldering="",
            soldered_by="",
            operating_time=1.0,
            defect=False,
            emission_spectrum=(),
            emission_spectrum_recorded_on="",
        ),
        led_back_intensity=1,
        led_back_distance_to_vial=1.0,
        led_back_exposure_time=duration_back,
        time_points_sample_taking=samples,
        size_sample=1.0,
        measurement_interval=measurement_interval,
        position_thermocouple="bla",
    )


def do_exp(
    lane: LedLane,
    duration_front: float,
    duration_back: float,
    samples: tuple[float, ...],
) -> ExperimentLogger:
    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(duration_front, duration_back, samples, 1.0)
    controller.supervisor.start_experiment_on(lane, template, 0, "")

    sample_time = 0
    for sample in samples:
        sample_time += sample

    time.sleep(max(max(duration_front, duration_back), sample_time) + 5)
    return logger


def assert_expirement_done(logger: ExperimentLogger, lane: LedLane):
    assert logger.done[lane]
    assert (
        logger.times_activation_led[lane] == logger.times_deactivation_led[lane]
    )


def test_simple_experiment():
    logger = do_exp(LedLane.LANE_1, 5.0, 5.0, ())
    assert_expirement_done(logger, LedLane.LANE_1)
    assert logger.times_activation_led[LedLane.LANE_1] == 2
    assert logger.times_deactivation_led[LedLane.LANE_1] == 2


def test_exp_with_samples():
    logger = do_exp(LedLane.LANE_1, 5, 5, (1, 2))
    assert_expirement_done(logger, LedLane.LANE_1)
    assert logger.times_samples[LedLane.LANE_1] == 2
    assert logger.times_activation_led[LedLane.LANE_1] == 6
    assert logger.times_deactivation_led[LedLane.LANE_1] == 6


def test_timing_of_samples():
    samples = (1, 2, 3, 2)
    logger = do_exp(LedLane.LANE_1, 10, 10, samples)
    assert_expirement_done(logger, LedLane.LANE_1)

    nr_sample = 0
    required_time = samples[nr_sample]
    for event in logger.log:
        if event.event == "[take sample]":
            assert event.timepoint < (required_time + 0.1)
            assert event.timepoint > (required_time - 0.1)
            nr_sample += 1
            if nr_sample == len(samples):
                break
            required_time += samples[nr_sample]


def test_timing_of_leds():
    logger = do_exp(LedLane.LANE_1, 1, 3, ())
    assert_expirement_done(logger, LedLane.LANE_1)
    nr_led = 0
    for event in logger.log:
        if event.event == "[deactivate LED]" and nr_led == 0:
            assert event.timepoint > 0.9
            assert event.timepoint < 1.1
            nr_led += 1
        elif event.event == "[deactivate LED]" and nr_led == 1:
            assert event.timepoint > 2.9
            assert event.timepoint < 3.1

    assert logger.log[-1].event == "[done]"
    assert logger.log[-1].timepoint > 2.9
    assert logger.log[-1].timepoint < 3.1


def test_samples_after_exposure():
    logger = do_exp(LedLane.LANE_1, 5, 6, (1, 3, 4, 10))

    assert_expirement_done(logger, LedLane.LANE_1)
    assert logger.log[-1].event == "[done]"
    assert logger.log[-1].timepoint > 17.9
    assert logger.log[-1].timepoint < 18.1

    assert logger.times_samples[LedLane.LANE_1] == 4

    assert logger.times_deactivation_led[LedLane.LANE_1] == 6


def test_measurements():
    logger = do_exp(LedLane.LANE_1, 6, 6, ())

    assert_expirement_done(logger, LedLane.LANE_1)
    assert len(logger.exp_data[LedLane.LANE_1].measured_data) <= 7
    assert len(logger.exp_data[LedLane.LANE_1].measured_data) >= 5


def test_register_event_and_error():
    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(5, 5, (), 1.0)
    controller.supervisor.start_experiment_on(LedLane.LANE_1, template, 0, "")
    time.sleep(1)
    controller.supervisor.register_error_on(LedLane.LANE_1)
    controller.supervisor.add_event_on(LedLane.LANE_1, "/Test/")
    time.sleep(5)

    assert_expirement_done(logger, LedLane.LANE_1)
    assert logger.exp_data[LedLane.LANE_1].error_occured

    exist_event = False

    for event in logger.exp_data[LedLane.LANE_1].event_log:
        if event.event == "/Test/":
            assert event.timepoint > 0.9
            assert event.timepoint < 1.1
            exist_event = True

    assert exist_event


def test_pause_resume():
    samples = (2, 2, 2)

    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(10, 10, samples, 1.0)
    controller.supervisor.start_experiment_on(LedLane.LANE_1, template, 0, "")
    time.sleep(1)
    controller.supervisor.pause_experiment_on(LedLane.LANE_1)
    time.sleep(1)
    controller.supervisor.resume_experiment_on(LedLane.LANE_1)
    time.sleep(2)
    controller.supervisor.pause_experiment_on(LedLane.LANE_1)
    time.sleep(1)
    controller.supervisor.resume_experiment_on(LedLane.LANE_1)
    time.sleep(9)

    assert_expirement_done(logger, LedLane.LANE_1)

    expected_sample_times = (3, 6, 8)
    expected_deactivate_times = (1, 1, 3, 3, 4, 4, 6, 6, 8, 8, 12, 12)
    expected_activate_times = (0, 0, 2, 2, 3, 3, 5, 5, 6, 6, 8, 8)

    deactivate_ctr = 0
    activate_ctr = 0
    sample_ctr = 0

    for event in logger.log:
        if event.event == "[deactivate LED]":
            assert deactivate_ctr < len(expected_deactivate_times)
            assert (
                event.timepoint
                > expected_deactivate_times[deactivate_ctr] - 0.1
            )
            assert (
                event.timepoint
                < expected_deactivate_times[deactivate_ctr] + 0.1
            )
            deactivate_ctr += 1
        elif event.event == "[activate LED]":
            assert activate_ctr < len(expected_activate_times)
            assert event.timepoint > expected_activate_times[activate_ctr] - 0.1
            assert event.timepoint < expected_activate_times[activate_ctr] + 0.1
            activate_ctr += 1
        elif event.event == "[take sample]":
            assert sample_ctr < len(expected_sample_times)
            assert event.timepoint > expected_sample_times[sample_ctr] - 0.1
            assert event.timepoint < expected_sample_times[sample_ctr] + 0.1
            sample_ctr += 1


def test_cancel():
    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(10, 10, (1, 2, 5), 1.0)
    controller.supervisor.start_experiment_on(LedLane.LANE_1, template, 0, "")
    time.sleep(5)
    controller.supervisor.cancel_experiment_on(LedLane.LANE_1)
    time.sleep(1)
    assert_expirement_done(logger, LedLane.LANE_1)
    assert logger.times_samples[LedLane.LANE_1] == 2
    time.sleep(6)  # Wait for possible second finish call


def test_double_pause():
    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(3, 3, (), 1.0)
    controller.supervisor.start_experiment_on(LedLane.LANE_1, template, 0, "")
    time.sleep(1)
    controller.supervisor.pause_experiment_on(LedLane.LANE_1)
    controller.supervisor.pause_experiment_on(LedLane.LANE_1)
    time.sleep(1)
    controller.supervisor.resume_experiment_on(LedLane.LANE_1)
    time.sleep(3)
    assert_expirement_done(logger, LedLane.LANE_1)


def test_double_resume():
    logger = ExperimentLogger()
    controller = MockController(logger)
    template = get_template_with(3, 3, (), 1.0)
    controller.supervisor.start_experiment_on(LedLane.LANE_1, template, 0, "")
    time.sleep(1)
    controller.supervisor.pause_experiment_on(LedLane.LANE_1)
    time.sleep(1)
    controller.supervisor.resume_experiment_on(LedLane.LANE_1)
    controller.supervisor.resume_experiment_on(LedLane.LANE_1)
    time.sleep(3)
    assert_expirement_done(logger, LedLane.LANE_1)
