import io
import typing as t
import tarfile


def make_tar_archive(files: t.Tuple[t.Union[str,
                                            t.Tuple[str, str],
                                            t.Tuple[io.BytesIO, str]]]) -> io.BytesIO:
    """
    :param files: iterable of either file paths or tuples (path, name)
    :return: io.BytesIO (not closed, for django save to FieldFile)
    """
    buffer = io.BytesIO()
    with tarfile.TarFile(fileobj=buffer, mode='w') as archive:
        for f in files:
            if isinstance(f, str):
                archive.add(f)
            else:
                target, name = f
                if isinstance(target, io.BytesIO):
                    tarinfo = tarfile.TarInfo(name=name)
                    tarinfo.size = len(target.getvalue())
                    archive.addfile(tarinfo, target)
                else:
                    archive.add(target, arcname=name)
    return buffer
