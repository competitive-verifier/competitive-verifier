// competitive-verifier: UNITTEST GOTESTRESULT

package main

import (
	"./helloworld"
	"testing"
)

func TestHelloWorld(t *testing.T) {
	want := "Hello World"
	if got := helloworld.GetHelloWorld(); got != want {
		t.Errorf("helloworld.GetHelloWorld() = %v, want %v", got, want)
	}
}
