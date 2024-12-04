import json

from cattrs import structure, unstructure

from prcontrol.controller.configuration import LED, EmmissionPair


def test_deserialise():
    json_string = """{
        "uid" : 0,
        "name" : "name",
        "fwhm" : 1,
        "max_of_emission" : 2,
        "min_wavelength" : 3,
        "max_wavelength" :4,
        "color" : "blue",
        "max_current" : 5,
        "manufacturer_id" : 6,
        "order_id" : 7,
        "date_soldering" : "2024-01-01",
        "soldered_by" : "Tim",
        "operating_time" : 8.0,
        "defect" : false,
        "emission_spectrum" : [
            {
                "wavelength" : 9,
                "intensity": 10.0
            },
            {
                "wavelength" : 11,
                "intensity": 12.0
            }
            ],
        "emission_spectrum_recorded_on" : "2023-01-01"
    }"""

    parsed_led = structure(json.loads(json_string), LED)

    assert parsed_led == LED(
        uid=0,
        name="name",
        fwhm=1,
        max_of_emission=2,
        min_wavelength=3,
        max_wavelength=4,
        color="blue",
        max_current=5,
        manufacturer_id=6,
        order_id=7,
        date_soldering="2024-01-01",
        soldered_by="Tim",
        operating_time=8.0,
        defect=False,
        emission_spectrum=(
            EmmissionPair(wavelength=9, intensity=10.0),
            EmmissionPair(wavelength=11, intensity=12.0),
        ),
        emission_spectrum_recorded_on="2023-01-01",
    )


def test_serialise_to_json():
    led = LED(
        uid=0,
        name="name",
        fwhm=1,
        max_of_emission=2,
        min_wavelength=3,
        max_wavelength=4,
        color="blue",
        max_current=5,
        manufacturer_id=6,
        order_id=7,
        date_soldering="2024-01-01",
        soldered_by="Tim",
        operating_time=8.0,
        defect=False,
        emission_spectrum=(
            EmmissionPair(wavelength=9, intensity=10.0),
            EmmissionPair(wavelength=11, intensity=12.0),
        ),
        emission_spectrum_recorded_on="2023-01-01",
    )

    # I am happy if json.loads produces the same python dict
    # as we do not want to test exact formatting.
    # However we need json.loads(json.dumps(...)) in order
    # to lower python tuples to arrays
    assert json.loads(json.dumps(unstructure(led))) == json.loads("""{
        "uid" : 0,
        "name" : "name",
        "fwhm" : 1,
        "max_of_emission" : 2,
        "min_wavelength" : 3,
        "max_wavelength" :4,
        "color" : "blue",
        "max_current" : 5,
        "manufacturer_id" : 6,
        "order_id" : 7,
        "date_soldering" : "2024-01-01",
        "soldered_by" : "Tim",
        "operating_time" : 8.0,
        "defect" : false,
        "emission_spectrum" : [
            {
                "wavelength" : 9,
                "intensity": 10.0
            },
            {
                "wavelength" : 11,
                "intensity": 12.0
            }
            ],
        "emission_spectrum_recorded_on" : "2023-01-01"
    }""")
