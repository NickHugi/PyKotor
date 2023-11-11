from pykotor.resource.formats.lip.lip_data import LIP, LIPKeyFrame


class DiffLIP:
    def __init__(self, old: LIP, new: LIP, log_func=print):
        self.old: LIP = old
        self.new: LIP = new
        self.log = log_func

    def compare_lip(self) -> bool:
        ret = True

        # Check for differences in the length attribute
        if self.old.length != self.new.length:
            self.log(f"Length mismatch: '{self.old.length}' --> '{self.new.length}'")
            ret = False

        # Check for keyframe mismatches
        old_frames = len(self.old)
        new_frames = len(self.new)

        if old_frames != new_frames:
            self.log(f"Keyframe count mismatch: {old_frames} --> {new_frames}")
            ret = False

        # Compare individual keyframes
        for i in range(min(old_frames, new_frames)):
            old_keyframe: LIPKeyFrame = self.old[i]
            new_keyframe: LIPKeyFrame = self.new[i]

            if old_keyframe.time != new_keyframe.time:
                self.log(f"Time mismatch at keyframe {i}: '{old_keyframe.time}' --> '{new_keyframe.time}'")
                ret = False

            if old_keyframe.shape != new_keyframe.shape:
                self.log(f"Shape mismatch at keyframe {i}: '{old_keyframe.shape.name}' --> '{new_keyframe.shape.name}'")
                ret = False

        return ret
