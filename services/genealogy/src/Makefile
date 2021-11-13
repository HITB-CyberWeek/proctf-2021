CC=gcc
CXX=g++
RM=rm -f

CPPFLAGS=-g -O0 -Wall -std=c++20 -Iinclude/ -I/usr/include/postgresql/
LDFLAGS=-g

SRCS=$(wildcard server/*.cpp) $(wildcard brotobuf/*.cpp) $(wildcard database/*.cpp) $(wildcard security/*.cpp) $(wildcard controllers/*.cpp) $(wildcard *.cpp)
OBJS=$(subst .cpp,.o,$(SRCS))
LDLIBS=libtaopq.a -lpq -lcrypto

main: $(OBJS)
	$(CXX) $(LDFLAGS) -o main $(OBJS) $(LDLIBS)

depend: .depend

.depend: $(SRCS)
	$(RM) ./.depend
	$(CXX) $(CPPFLAGS) -MM $^>>./.depend;

clean:
	$(RM) $(OBJS)

distclean: clean
	$(RM) *~ .depend

include .depend
