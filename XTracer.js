function log(text) {
    var packet = {
        'cmd': 'log',
        'data': text
    };
    send("XTracer:::" + JSON.stringify(packet))
}

function enter(tid, cls, method, args) {
    var packet = {
        'cmd': 'enter',
        'data': [tid, cls, method, args]
    };
    send("XTracer:::" + JSON.stringify(packet))
}

// function exit(tid, retval) {
//     var packet = {
//         'cmd': 'exit',
//         'data': [tid, retval]
//     };
//     send("XTracer:::" + JSON.stringify(packet))
// }

function getTid() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getId();
}

function getTName() {
    var Thread = Java.use("java.lang.Thread")
    var currentThread = Thread.currentThread()
    return currentThread.getName();
}

function overloads(target, clsname, methodName) {
    var overloads = target[methodName].overloads;
    overloads.forEach(function (overload) {
        var proto = "(";
        overload.argumentTypes.forEach(function (type) {
            proto += type.className + ", ";
        });
        if (proto.length > 1) {
            proto = proto.substr(0, proto.length - 2);
        }
        proto += ")";
        log("hooking: " + clsname + "." + methodName + proto);
        overload.implementation = function () {
            var args = [];
            var tid = getTid();
            var tName = getTName();
            for (var j = 0; j < arguments.length; j++) {
                args[j] = arguments[j] + ""
            }
            enter(tid, clsname, methodName + proto, args);
            // enter(tid, tName, clsname, methodName + proto, args);
            var retval = this[methodName].apply(this, arguments);
            // exit(tid, "" + retval);
            return retval;
        }
    });
}

function traceClass(clsname, method_name, JavaLoader) {
    try {
        var target = (JavaLoader === undefined) ? Java.use(clsname) : JavaLoader.use(clsname)
        if (method_name === '') {
            var methods = target.class.getDeclaredMethods();
            console.log(methods)
            methods.forEach(function (method) {
                var methodName = method.getName()
                overloads(target, clsname, methodName)
            });
        } else {
            overloads(target, clsname, method_name)
        }
        return true
    } catch (e) {
        log("[P] fail hook '" + clsname + "' hook fail: " + e)
        return false
    }
}

function match(ex, text) {
    if (ex.indexOf('/') != -1) {
        var method = ex.split('/')[1]
        ex = ex.split('/')[0]
        return [ex == text, method];
    } else
        return [text.match(ex), '']
}

if (Java.available) {
    Java.perform(function () {
        log('[A] ZenTracer Start...');
        // var hook_list = [
        //     //intent
        //     'android.content.Intent/$init',
        //     'android.content.Intent/putExtra',
        //     'android.content.Intent/setAction',
        //     //permission
        //     'android.support.v4.app.ActivityCompat/requestPermissions',
        //     'androidx.core.app.ActivityCompat/requestPermissions',
        //     // telephony
        //     'android.telephony.TelephonyManager/getDeviceId',
        //     'android.telephony.TelephonyManager/getImei',
        //     'android.telephony.TelephonyManager/getMeid',
        //     'android.telephony.TelephonyManager/getSimSerialNumber',
        //     'android.telephony.TelephonyManager/getSubscriberId',
        //     'android.telephony.TelephonyManager/getSimOperator',
        //     'android.telephony.TelephonyManager/getNetworkOperator',
        //     'android.telephony.TelephonyManager/getSimCountryIso',
        //     'android.telephony.TelephonyManager/getCellLocation',
        //     'android.telephony.TelephonyManager/getAllCellInfo',
        //     'android.telephony.TelephonyManager/requestCellInfoUpdate',
        //     'android.telephony.TelephonyManager/getServiceState',
        //     'android.telephony.cdma.CdmaCellLocation/getBaseStationId',
        //     'android.telephony.cdma.CdmaCellLocation/getNetworkId',
        //     'android.telephony.gsm.GsmCellLocation/getCid',
        //     'android.telephony.gsm.GsmCellLocation/getLac',
        //     // address
        //     'android.provider.Settings$Secure/getString',
        //     'android.os.Build/getSerial',
        //     'android.app.admin.DevicePolicyManager/getWifiMacAddress',
        //     'android.content.ClipboardManager/getPrimaryClip',
        //     // package
        //     'android.content.pm.PackageManager/getInstalledPackages',
        //     'android.content.pm.PackageManager/getInstalledApplications',
        //     'android.app.ApplicationPackageManager/getInstalledPackages',
        //     'android.app.ApplicationPackageManager/getInstalledApplications',
        //     'android.app.ApplicationPackageManager/queryIntentActivities',
        //     'android.app.ApplicationPackageManager/getInstallerPackageName',
        //     'android.app.ApplicationPackageManager/getPackageInfoAsUser',
        //     'android.app.ActivityManager/getRunningAppProcesses',
        //     // package
        //     'android.app.ApplicationPackageManager/getApplicationInfo',
        //     // manage
        //     'android.location.LocationManager/requestLocationUpdates',
        //     'android.location.LocationManager/getLastKnownLocation',
        //     // camera
        //     'android.hardware.Camera/open',
        //     'android.hardware.camera2.CameraManager.Camera/openCamera',
        //     'androidx.camera.core.ImageCapture/takePicture',
        //     // wifi address
        //     'android.net.wifi.WifiInfo/getMacAddress',
        //     'android.net.wifi.WifiInfo/getSSID',
        //     'android.net.wifi.WifiInfo/getBSSID',
        //     // wifi
        //     'android.net.wifi.WifiInfo/getIpAddress',
        //     'android.net.wifi.WifiManager/getConnectionInfo',
        //     'android.net.wifi.WifiManager/getConfiguredNetworks',
        //     'android.net.wifi.WifiManager/getScanResults',
        //     'java.net.InetAddress/getHostAddress',
        //     'java.net.NetworkInterface/getHardwareAddress',
        //     'android.net.NetworkInfo/getType',
        //     'android.net.NetworkInfo/getTypeName',
        //     'android.net.NetworkInfo/getExtraInfo',
        //     'android.net.NetworkInfo/isConnected',
        //     // bluetooth
        //     'android.bluetooth.BluetoothDevice/getName',
        //     'android.bluetooth.BluetoothDevice/getAddress',
        //     'android.bluetooth.BluetoothAdapter/getName'
        // ];
        var hook_list = {hook_list};
        Java.enumerateLoadedClasses({
            onMatch: function (aClass) {
                for (var index in hook_list) {
                    var api_method = match(hook_list[index], aClass)
                    if (api_method[0]) {
                        if (traceClass(aClass, api_method[1])) {
                            log("[B] match '" + hook_list[index] + "'");
                        }
                    }
                }
            },
            onComplete: function () {
                log("[B] Loaded Class hooked.");
            }
        });
        Java.enumerateClassLoaders({
            onMatch: function (aloader) {
                for (var index in hook_list) {
                    try {
                        var targetClass = hook_list[index].split('/')[0]
                        var targetMethod = hook_list[index].split('/')[1]
                        if (aloader.toString().startsWith(targetClass)) {
                            Java.classFactory.loader = aloader
                            if (traceClass(targetClass, targetMethod, Java.classFactory)) {
                                log("[C] catch " + hook_list[index]);
                            }
                        }
                    } catch (err) {
                        console.log(err)
                    }
                }
            },
            onComplete: function () {
                log("[C] Dynamic Class hooked.");
            }
        })
    });
    //send complete log !important
    log("Hook Complete");
} else {
    log('Java error')
}