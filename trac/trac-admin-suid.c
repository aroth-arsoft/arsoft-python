#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

int main(int argc, char ** argv, char ** env)
{
    const char * trac_admin = "/usr/bin/trac-admin";
    char ** trac_admin_argv = NULL;
    int i;
    //int uid;
    uid_t euid;
    gid_t egid;
    trac_admin_argv = (char **)malloc(sizeof(char*) * (argc + 1));
    trac_admin_argv[0] = (char*)trac_admin;
    for(i = 1; i < argc; i++)
        trac_admin_argv[i] = argv[i];
    trac_admin_argv[argc] = NULL;
	// because of the extra security of bash (and/or other shells), the shell will set the
	// effective uid (EUID) back to the real uid (RUID), which causes the script to run
	// without root permissions. Happens on Ubuntu 11.10.
	// see 
	// http://stackoverflow.com/questions/556194/calling-a-script-from-a-setuid-root-c-program-script-does-not-run-as-root
    //uid = getuid();
    euid = geteuid();
    egid = getegid();
    //printf("euid=%i, egid=%i\n", euid, egid);
	if(setuid(euid) != 0)
        fprintf(stderr, "setuid(%i) failed\n", euid);
    if(setgid(egid) != 0)
        fprintf(stderr, "setgid(%i) failed\n", egid);
    //printf("euid=%i\n", euid);
	// start the script with the parameters
    return execve(trac_admin, trac_admin_argv, env);
}
