# EvilRMI

## What is it?

EvilRMI is a (very) simple implementation of the [VeraCode JNDI research](https://www.veracode.com/blog/research/exploiting-jndi-injections-java) with a few additional features:

* Supports ScriptEngineFactory and SnakeYAML payloads
* Includes an easily modifiable remote class load payload
* RMI proxy for environments where outbound network connections are limited

## Prep

Edit the following files to do what you need them to do:

* src/payload/java/org/rxb/EvilScriptEngineFactory.java
* resources/payload.js
* resources/payload.yml

## Build

`./compile.sh`

## Run

`./run.sh` <hostname/IP> <port> <js|yml> <path to payload>

## RMI Proxy

Exploiting RMI lookups in environments where network ACLs restrict outbound connections is problematic. We can host the RMI Registry on an arbitrary port (e.g. 443) to make it reachable from a network that only allows 80/tcp and 443/tcp outbound for example, but we still have a problem - the RMI object will be bound to a (random) ephemeral port on the server hosting EvilRMIServer. The victim will be able to query the RMI Registry, but it won't be able to retrieve the object. Sad times.

The proxy intercepts RMI Registry lookups, and rewrites the return message, modifying the port field. This means we can cause the victim to request the object from a port it can open connections to (e.g. 80/tcp), and we proxy the request to the real port.
