import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

void main() {
  FlutterBluePlus.setLogLevel(LogLevel.verbose, color: true);
  runApp(const BleApp());
}

class BleApp extends StatelessWidget {
  const BleApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ble Config',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const BleHomePage(),
    );
  }
}

class BleHomePage extends StatefulWidget {
  const BleHomePage({super.key});
  @override
  State<BleHomePage> createState() => _BleHomePageState();
}

class _BleHomePageState extends State<BleHomePage> {
  // 是否授权蓝牙
  bool _isPermissionGranted = false;

  @override
  void initState() {
    super.initState();
    // 检查权限
    var subscription = FlutterBluePlus.adapterState.listen((state) {
      if (state == BluetoothAdapterState.on) {
        _isPermissionGranted = true;
      } else {
        _showNotifyText('未授权蓝牙权限');
      }
    });
    subscription.cancel();
  }

  // 显示提示语
  void _showNotifyText(notifyText) {
    final snackBar = SnackBar(
      content: Text(notifyText),
      duration: const Duration(seconds: 3),
    );
    ScaffoldMessenger.of(context).showSnackBar(snackBar);
  }

  // 开始扫描BLE设备
  void startScan() {
    // setState(() {
    //   isScanning = true;
    //   devices.clear();  // 每次扫描清空设备列表
    // });

    // flutterBlue.startScan(timeout: Duration(seconds: 5)).listen((scanResult) {
    //   setState(() {
    //     // 根据设备ID去重
    //     devices[scanResult.device.id.id] = scanResult.device;
    //   });
    // }, onDone: () {
    //   setState(() {
    //     isScanning = false;
    //   });
    // });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BLE Device Config'),
      ),
      body: Column(
        children: [
          if (true ) //!isScanning && connectedDevice == null
            ElevatedButton(
              onPressed: startScan,
              child: const Text('扫描BLE设备'),
            ),
          // Expanded(
          //   child: ListView(
          //     children: devices.values.map((device) {
          //       return ListTile(
          //         title: Text(device.name.isNotEmpty ? device.name : '未知设备'),
          //         subtitle: Text(device.id.id),
          //         trailing: connectedDevice == null
          //             ? ElevatedButton(
          //                 onPressed: () => connectToDevice(device),
          //                 child: Text('连接'),
          //               )
          //             : null,
          //       );
          //     }).toList(),
          //   ),
          // ),
          // if (connectedDevice != null) ...[
          //   Padding(
          //     padding: const EdgeInsets.all(8.0),
          //     child: Text('已连接设备: ${connectedDevice!.name}'),
          //   ),
          //   DropdownButton<String>(
          //     value: selectedOption,
          //     hint: Text('选择一个选项'),
          //     onChanged: (String? newValue) {
          //       setState(() {
          //         selectedOption = newValue;
          //       });
          //       if (newValue != null) {
          //         sendDataToBLE(newValue);
          //       }
          //     },
          //     items: options.map<DropdownMenuItem<String>>((String value) {
          //       return DropdownMenuItem<String>(
          //         value: value,
          //         child: Text(value),
          //       );
          //     }).toList(),
          //   ),
          // ]
        ],
      ),
    );
  }
}
