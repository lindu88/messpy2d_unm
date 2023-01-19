import h5py


def flat_attr(grp: h5py.Group, d: dict):
    """Flatten a dictionary and write it to the group attributes."""
    for k, v in d.items():
        if isinstance(v, dict):
            flat_attr(grp.create_group(k), v)
        else:
            grp.attrs[k] = v


def test_meta_attrs(tmp_path):
    """Test that meta attrs are written to the file."""
    test_dict = {"test": "test",
                 "test2": "test2",
                 "test_dict": {"test": "test", },
                 "test_dict2": {'dict': {'test': 'test'}, },
                 }

    path = tmp_path / "test.h5"
    with h5py.File(path, "w") as f:
        f.create_group("test")
        flat_attr(f["test"], test_dict)

    with h5py.File(path, "r") as f:
        for k, v in test_dict.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    assert f["test"][k][k2].attrs[k2] == v2
            else:
                assert f["test"].attrs[k] == v
