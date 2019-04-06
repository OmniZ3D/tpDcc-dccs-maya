from tpPyUtils import enum


class DebugLevel(enum.Enum):
    pass


class ScriptLanguage(enum.Enum):
    pass


class DebugLevels(enum.EnumGroup):
    Disabled = DebugLevel(0)
    Low = DebugLevel()
    Mid = DebugLevel()
    High = DebugLevel()


class ScriptLanguages(enum.EnumGroup):
    Python = ScriptLanguage()
    MEL = ScriptLanguage()
    CSharp = ScriptLanguage()
    CPlusPlus = ScriptLanguage()
    Manifest = ScriptLanguage()
