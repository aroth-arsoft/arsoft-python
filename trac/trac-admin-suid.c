#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

int switch_to_user()
{
    int ret;
    uid_t euid = geteuid();
    gid_t egid = getegid();

    // because of the extra security of bash (and/or other shells), the shell will set the
    // effective uid (EUID) back to the real uid (RUID), which causes the script to run
    // without root permissions. Happens on Ubuntu 11.10.
    // see 
    // http://stackoverflow.com/questions/556194/calling-a-script-from-a-setuid-root-c-program-script-does-not-run-as-root

    ret = setuid(euid);
    if(ret != 0)
    {
        char * errorno_msg = strerror(errno);
        fprintf(stderr, "Failed to set UID to %i, error %i %s\n", euid, errno, errorno_msg);
    }
    else
    {
        ret = setgid(egid);
        if(ret != 0)
        {
            char * errorno_msg = strerror(errno);
            fprintf(stderr, "Failed to set GID to %i, error %i %s\n", egid, errno, errorno_msg);
        }
    }
    return ret;
}

int main(int argc, char ** argv, char ** env)
{
    const char * target_executable = "/usr/bin/trac-admin";
    char ** target_argv = NULL;
    int i, ret;

    target_argv = (char **)malloc(sizeof(char*) * (argc + 1));
    target_argv[0] = (char*)target_executable;
    for(i = 1; i < argc; i++)
        target_argv[i] = argv[i];
    target_argv[argc] = NULL;

    ret = switch_to_user();
    if(!ret)
    {
        // start the script with the parameters
        ret = execve(target_executable, target_argv, env);
    }
    return ret;
}
