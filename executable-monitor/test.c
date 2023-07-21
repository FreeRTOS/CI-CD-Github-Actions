#include <sys/time.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

typedef struct DateAndTime
{
    int year;
    int month;
    int day;
    int hour;
    int minutes;
    int seconds;
    int msec;
} DateAndTime;

int main( int argc,
          char ** argv )
{
    DateAndTime date_and_time;
    struct timeval tv;
    struct tm * tm;
    int32_t loop = 0;
    int32_t totalLoops = 5;
    int32_t exitCode = 0;

    if( argc == 1 )
    {
        printf( "This is a basic test application.\n" );
        printf( "It prints the date and time and then sleeps for loopCount * 3\n" );
        printf( "This program takes in two inputs, a loop count and an exit code\n" );
        printf( "By default it will run 5 loops and exit with exit status 0\n" );
    }

    if( argc == 2 )
    {
        totalLoops = ( int32_t ) atoi( argv[ 2 ] );
        printf( "Will run for requested %d loops\n", totalLoops );
    }

    if( argc == 3 )
    {
        exitCode = atoi( argv[ 3 ] );
        printf( "Will exit with supplied exit code %d\n", exitCode );
    }

    setvbuf( stdout, NULL, _IONBF, 0 );

    for(int i = 1; i < totalLoops; i++)
    {
        gettimeofday( &tv, NULL );
        tm = localtime( &tv.tv_sec );
        /* Add 1900 to get the right year value */
        /* read the manual page for localtime() */
        /* date_and_time.year = tm->tm_year + 1900; */
        /* Months are 0 based in struct tm */
        date_and_time.year = tm->tm_year + 1900;
        date_and_time.month = tm->tm_mon + 1;
        date_and_time.day = tm->tm_mday;
        date_and_time.hour = tm->tm_hour;
        date_and_time.minutes = tm->tm_min;
        date_and_time.seconds = tm->tm_sec;
        date_and_time.msec = ( int ) ( tv.tv_usec / 1000 );

        fprintf( stdout, "%02d:%02d:%02d.%03d %02d-%02d-%04d TEST APPLICIATION SLEEPING FOR %d SECONDS\n",
                 date_and_time.hour,
                 date_and_time.minutes,
                 date_and_time.seconds,
                 date_and_time.msec,
                 date_and_time.day,
                 date_and_time.month,
                 date_and_time.year,
                 i * 3U
                 );
        sleep( i * 3U );
    }

    printf( "EXITING TEST APPLICICATION WITH EXIT CODE = %d\n",exitCode );
    return exitCode;
}
