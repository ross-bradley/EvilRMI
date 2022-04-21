
#!/bin/bash
javac --add-modules jdk.naming.rmi --add-exports jdk.naming.rmi/com.sun.jndi.rmi.registry=ALL-UNNAMED  -cp ./deps/tomcat-catalina-9.0.37.jar src/server/java/org/rxb/EvilRMIServer.java
mv src/server/java/org/rxb/EvilRMIServer.class build/org/rxb

javac src/payload/java/org/rxb/EvilScriptEngineFactory.java
jar -cf build/EvilScriptEngineManager-payload.jar -C src/payload/java/ .
