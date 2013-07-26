#include <stdio.h>
#include <unistd.h>

int main(int argc, char ** argv, char ** env)
{
    const char * edskmgr = "/usr/bin/edskmgr";
    int ret = 0;
    char * const edskmgr_argv[] = {
		(char *)edskmgr,
#ifdef EDSKMGR_LOAD
		"--load",
#elif EDSKMGR_EJECT
		"--eject",
#else
#error no edskmgr operation defined
#endif
	NULL
    };
	// because of the extra security of bash (and/or other shells), the shell will set the
	// effective uid (EUID) back to the real uid (RUID), which causes the script to run
	// without root permissions. Happens on Ubuntu 11.10.
	// see 
	// http://stackoverflow.com/questions/556194/calling-a-script-from-a-setuid-root-c-program-script-does-not-run-as-root
	ret = setuid(0);
    if(!ret)
    {
        // start the script with the parameters
        ret = execve(edskmgr, edskmgr_argv, env);
    }
    else
        ret = -1;
    return ret;
}
