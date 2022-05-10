python early in jn_data_migrations:
    from enum import Enum
    import re
    from renpy.store import persistent

    # dict mapping a from_version -> to_version, including the function used to migrate between those versions
    # form:
    # "x.y.z": {
    #    MigrationRuntimes.INIT: (callable, "x.y.z"),
    #    MigrationRuntimes.RUNTIME: (callable, "x.y.z")
    #},
    UPDATE_FUNCS = dict()

    # list containing the late (during runtime) migrations we need to run. These will simply be run in order.
    LATE_UPDATES = []

    #Parses x.x.x.x (suffix) to a regex match with two groups:
    # ver and suffix
    VER_STR_PARSER = re.compile(r"^(?P<ver>\d+\.\d+\.\d+)(?P<suffix>.*)$")

    class MigrationRuntimes(Enum):
        """
        Enum for the times to run migration scripts.
        """
        INIT = 1
        RUNTIME = 2

    def migration(from_versions, to_version, runtime=MigrationRuntimes.INIT):
        """
        Decorator function to register a data migration function

        IN:
            from_versions: list of versions to migrate from
            to_version: version to migrate to
            during_runtime: whether the migration is run during runtime. If False, it is run during init 10
                (Default: MigrationRuntimes.INIT)

        OUT:
            the wrapper function
        """
        def wrap(_function):
            registerUpdateFunction(
                _function,
                from_versions,
                to_version,
                during_runtime
            )
            return _function
        return wrap

    def registerUpdateFunction(_callable, from_versions, to_version, runtime=MigrationRuntimes.INIT):
        """
        Register a function to be called when the program is updated.

        IN:
            _callable: the function to run (Must take no arguments)
            from_versions: list of versions to migrate from
            to_version: version to migrate to
            during_runtime: whether the migration is run during runtime. If False, it is run during init 10
                (Default: MigrationRuntimes.INIT)
        """
        for from_version in from_versions:
            if from_version not in UPDATE_FUNCS:
                UPDATE_FUNCS[from_version] = dict()

            UPDATE_FUNCS[from_version][runtime] = (_callable, to_version)

    def ver_string_to_ver_list(ver_str):
        """
        Converts a version string to a list of integers representing the version.
        """
        match = VER_STR_PARSER.match(ver_str)
        if not match:
            raise ValueError("Invalid version string.")

        ver_list = match.group("ver").split(".")
        return [int(x) for x in ver_list]

    def compare_versions(ver_str1, ver_str2):
        """
        Compares two version strings.
        """
        match1 = VER_STR_PARSER.match(ver_str1)
        match2 = VER_STR_PARSER.match(ver_str2)

        if not match1 or not match2:
            raise ValueError("Invalid version string.")

        ver1 = ver_string_to_ver_list(match1.group("ver"))
        ver2 = ver_string_to_ver_list(match2.group("ver"))

        #Check the lengths of the versions, we'll pad the shorter one with zeros
        if len(ver1) > len(ver2):
            ver2 += [0] * (len(ver1) - len(ver2))
        elif len(ver1) < len(ver2):
            ver1 += [0] * (len(ver2) - len(ver1))

        #Now directly compare from left to right
        for i in range(len(ver1)):
            if ver1[i] > ver2[i]:
                return 1
            elif ver1[i] < ver2[i]:
                return -1

        #If we got here, the versions are equal
        return 0

    def runInitMigrations():
        """
        Runs init time migration functions. Must be run after init 0
        """
        #We do nothing here if the version isn't in the dict
        if persistent._jn_version not in UPDATE_FUNCS:
            return

        #Set to_version to the version we're migrating from
        to_version = persistent._jn_version

        while compare_versions(to_version, renpy.config.version) < 0:
            #First, check if there's a late migration we need to run
            if MigrationRuntimes.RUNTIME in UPDATE_FUNCS[persistent._jn_version]:
                LATE_UPDATES.append(UPDATE_FUNCS[persistent._jn_version][MigrationRuntimes.RUNTIME])

            #We're below the latest version, so we need to migrate to the next one in the chain
            _callable, to_version = UPDATE_FUNCS[to_version][MigrationRuntimes.RUNTIME]

            #Migrate
            _callable()

    def runRuntimeMigrations():
        """
        Runs the runtime migration functions.
        """
        for _callable in LATE_UPDATES:
            _callable()

#Init time migrations are run at init 10
init 10 python:
    jn_data_migrations.runInitMigrations()

init python in jn_data_migrations: