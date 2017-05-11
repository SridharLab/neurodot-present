from collections import OrderedDict

_settings = OrderedDict()
_settings['vsync_version'] = 1


def get_class_VsyncPatch():
    #check to see which version of the VsyncPatch we should export
    if _settings['vsync_version'] == 1:
        from vsync_patch import VsyncPatch_Version1 as VsyncPatch
        return VsyncPatch
    elif _settings['vsync_version'] == 2:
        from vsync_patch import VsyncPatch_Version2 as VsyncPatch
        return VsyncPatch
    else:
        raise ValueError("bad setting of 'vsync_version', settings: %r" % settings)
