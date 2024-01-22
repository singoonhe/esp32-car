using System;
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;

public class CarObject : MonoBehaviour
{
    private UdpClient udpClient;
    private int port = 7890;
    private string serverIP = "192.168.3.199"; // 目标IP地址
    // private IPEndPoint endPoint;

    private void Start()
    {
        udpClient = new UdpClient();
        udpClient.Connect(serverIP, port);
        udpClient.BeginReceive(new AsyncCallback(OnReceived), udpClient);
        // endPoint = new IPEndPoint(IPAddress.Parse(serverIP), port);
    }

    public void StartConnect()
    {
        // 发送登录命令
        SendCmdData("Login");
    }

    public void SendCmdData(string typeName, string typeValue = null)
    {
            Debug.Log("Sent: SendCmdData");
        // if (udpClient.Available > 0){
            string send_msg = $"{{\"Type\":\"{typeName}\"";
            if (typeValue != null)
            {
                send_msg = send_msg + $", \"Value\":\"{typeValue}\"";
            }
            send_msg = send_msg + "}";
            byte[] data = Encoding.UTF8.GetBytes(send_msg);
            udpClient.Send(data, data.Length);
            Debug.Log("Sent: " + send_msg);
        // }
    }

    void OnReceived(IAsyncResult result)
    {
        UdpClient socket = result.AsyncState as UdpClient;
        // points towards whoever had sent the message:
        IPEndPoint source = new IPEndPoint(0, 0);
        // get the actual message and fill out the source:
        byte[] message = socket.EndReceive(result, ref source);
        string returnData = Encoding.UTF8.GetString(message);
        Debug.Log("Got this: " + returnData);
        socket.BeginReceive(new AsyncCallback(OnReceived), socket);
    }
    
    // private void Update()
    // {
    //     if (udpClient.Available > 0)
    //     {
    //         ReceiveData();
    //     }
    // }

    // private async void ReceiveData()
    // {
    //     UdpReceiveResult result = await udpClient.ReceiveAsync();
    //     byte[] receivedData = result.Buffer;
    //     string receivedMessage = Encoding.UTF8.GetString(receivedData);
    //     Debug.Log("Received: " + receivedMessage);
    // }

    private void OnDestroy()
    {
        udpClient.Close();
    }
}