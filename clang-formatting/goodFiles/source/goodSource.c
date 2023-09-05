#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct DateAndTime
{
    uint64_t hour;
    uint64_t minutes;
    uint64_t seconds;
    uint64_t msec;
} DateAndTime;

#if defined( WIN32 ) || defined( _WIN32 ) || defined( __WIN32__ ) || \
    defined( __NT__ ) || defined( WIN64 ) || defined( __WIN64 )
    #include <Windows.h>
/* Remove the warning about implicit sleep even with windows.h included */
extern void sleep( int miliseconds );
void getTime( struct DateAndTime * currentTime )
{
    SYSTEMTIME st, lt;

    GetLocalTime( &lt );
    currentTime->hour = lt.wHour;
    currentTime->minutes = lt.wMinute;
    currentTime->seconds = lt.wSecond;
    currentTime->msec = lt.wMilliseconds;
}
#else /* if defined( WIN32 ) || defined( _WIN32 ) || defined( __WIN32__ ) || \
         defined( __NT__ ) || defined( WIN64 ) || defined( __WIN64 ) */
    #include <sys/time.h>
    #include <unistd.h>
void getTime( struct DateAndTime * currentTime )
{
    struct timeval tv;
    struct tm * tm;

    gettimeofday( &tv, NULL );
    tm = localtime( &tv.tv_sec );
    currentTime->hour = tm->tm_hour;
    currentTime->minutes = tm->tm_min;
    currentTime->seconds = tm->tm_sec;
    currentTime->msec = ( int ) ( tv.tv_usec / 1000 );
}
#endif /* if defined( WIN32 ) || defined( _WIN32 ) || defined( __WIN32__ ) || \
          defined( __NT__ ) || defined( WIN64 ) || defined( __WIN64 ) */

int main( int argc, char ** argv )
{
    DateAndTime currentTime = { 0 };
    int32_t loop = 0;
    int32_t totalLoops = 5U;
    int32_t exitCode = 0;

    if( argc == 1 )
    {
        printf( "This is a basic test application.\n" );
        printf(
            "It prints the date and time and then sleeps for loopCount * 3\n" );
        printf( "This program takes in two inputs, a loop count and an exit "
                "code\n" );
        printf( "By default it will run %d loops and exit with exit status "
                "%d\n",
                totalLoops,
                exitCode );
    }

    if( argc == 2 )
    {
        totalLoops = atoi( argv[ 1 ] );
        printf( "Will run for requested %d loops\n", totalLoops );
    }

    if( argc == 3 )
    {
        exitCode = atoi( argv[ 2 ] );
        printf( "Will exit with supplied exit code %d\n", exitCode );
    }

    setvbuf( stdout, NULL, _IONBF, 0 );

    for( int i = 1U; i < totalLoops; i++ )
    {
        getTime( &currentTime );
        printf( "%02llu:%02llu:%02llu.%03llu TEST APPLICATION SLEEPING FOR %d "
                "SECONDS\n",
                currentTime.hour,
                currentTime.minutes,
                currentTime.seconds,
                currentTime.msec,
                i * 3U );
        sleep( i * 3U );
    }

#ifdef EXIT_WITH_MINUTES
    exitCode = currentTime.minutes;
#endif
    printf( "EXITING TEST APPLICATION WITH EXIT CODE = %d\n", exitCode );
    return exitCode;
}
