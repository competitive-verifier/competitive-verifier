import posixpath


# NOTE: We should use this instead of posixpath.normpath
# posixpath.normpath doesn't collapse a leading duplicated slashes.
# see: https://stackoverflow.com/questions/7816818/why-doesnt-os-normpath-collapse-a-leading-double-slash
def normpath(path: str) -> str:
    path = posixpath.normpath(path)
    if path.startswith("//"):
        path = "/" + path.lstrip("/")
    return path
