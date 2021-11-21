package main

import (
	"fmt"
	"github.com/tebeka/selenium"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
//	"os"
	"strings"
)

const (
	chromedriverPath = "/usr/local/bin/chromedriver"
	chromedriverPort = 9515
	port             = 4444
)

func main() {
	ops := []selenium.ServiceOption{
//		selenium.Output(os.Stderr),
	}
	service, err := selenium.NewChromeDriverService(chromedriverPath, chromedriverPort, ops...)
	if err != nil {
		fmt.Printf("Error starting the ChromeDriver server: %v", err)
		panic(err)
	}
	defer service.Stop()

	origin, _ := url.Parse(fmt.Sprintf("http://localhost:%d/", chromedriverPort))

	director := func(req *http.Request) {
		req.URL.Scheme = "http"
		req.URL.Host = origin.Host
		req.Host = origin.Host

		if !strings.HasPrefix(req.Header.Get("Origin"), "http") {
			req.Header.Del("Origin")
		}
		if !strings.HasPrefix(req.Header.Get("Referer"), "http") {
			req.Header.Del("Referer")
		}
	}

	proxy := &httputil.ReverseProxy{Director: director}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		proxy.ServeHTTP(w, r)
	})

	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
