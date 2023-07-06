package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
)

func echo(s net.Conn, i int) {
	defer s.Close()

	fmt.Printf("%d: %v <-> %v\n", i, s.LocalAddr(), s.RemoteAddr())
	b := bufio.NewReader(s)
	for {
		line, e := b.ReadBytes('\n')
		if e != nil {
			break
		}
		s.Write(line)
	}
	fmt.Printf("%d: closed\n", i)
}

func main() {
	echoPort := "7"
	if len(os.Args) <= 1 {
		fmt.Printf("Using a default port of 7\n")
	} else {
		echoPort = os.Args[1]
		echoPortInt, err := strconv.Atoi(echoPort)
		if (echoPortInt < 0 || echoPortInt > 10000) || (err != nil) {
			fmt.Printf("Provided echo port of \"%s\" is not a valid integer\n", echoPort)
			log.Fatal(err)
		}
	}
	fmt.Printf("Creating an echo server on port: %s\n", echoPort)
	l, e := net.Listen("tcp", ":"+echoPort)
	for i := 0; e == nil; i++ {
		var s net.Conn
		s, e = l.Accept()
		go echo(s, i)
	}
}
