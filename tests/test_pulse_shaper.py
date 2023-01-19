from unittest.mock import MagicMock
from MessPy.Instruments.dac_px import AOM
from pytest import raises


def test_aom():
    mock_dac = MagicMock()
    aom = AOM(dac=mock_dac)

    # with raises(ValueError):
    #    aom.double_pulse(4, 0.1, 1600)

    aom.load_calib_mask()
    print(aom.mask.shape)

    p1 = 23.334e-9
    p2 = -1.943e-3
    p3 = 67.4
    aom.set_calib((p1, p2, p3))
    aom.generate_waveform()

    masks = aom.double_pulse(1, 0.1, 1600)
    assert(masks[0].shape[0] == len(aom.nu))
    assert(masks[0].shape[1] == 11*4)

    aom.bragg_wf(masks[0], masks[1])
    aom.classic_wf(masks[0], masks[1])

    aom.generate_waveform()
    aom.bragg_wf(1, 1)
    aom.classic_wf(1, 1)
