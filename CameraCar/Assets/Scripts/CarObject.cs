using System;
using UnityEngine;
using UnityEngine.UI;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine.EventSystems;
using UnityEngine.Events;
using System.IO;
using BestHTTP.JSON;
using System.Collections.Generic;
using System.Linq;
using System.Collections;

public class CarObject : MonoBehaviour
{
    private string      configPath;
    private UdpClient   udpClient = null;
    private int         dstPort = 7890;
    private int         heartCount = 0;//心跳
    private Coroutine   timerCoroutine;// 网络连接检查器
    private int         dirPointId = -1;
    private Vector2     dirOrginPos;    // 方向键的原始位置
    private int         speedPointId = -1;
    private const float dirMoveDis = 75; // 方向键移动的最大距离
    private int         sendDirValue = -1;  // 移动的方向值
    private int         sendSpeedValue = 6;// 移动的速度值
    // 绑定结点
    public InputField   ipInput;
    public Text         ipText;     // ip地址显示栏
    public Text         speedText;  // 速度显示栏
    public Image        wifiImg;    // wifi状态显示
    public Image        dirImg;     // 左侧方向拖动的图
    public Image        dirBgImg;   // 左侧方向的背景图
    public Image        speedImg;   // 右侧速度拖动的图
    public Image        speedBgImg; // 右侧速度的背景图
    public RawImage     frameImg;   // 摄像机显示图
    // 按钮状态图
    public Sprite       wifiOff;    // wifi已连接状态图
    public Sprite       wifiOn;     // wifi未连接状态图

    // udp接收到的数据
    Dictionary<int, Dictionary<int, byte[]>> receivedSlices = new Dictionary<int, Dictionary<int, byte[]>>();
    Queue<int> receivedFrameQueue = new Queue<int>();

    private void Start()
    {
        dirOrginPos = new Vector2(dirImg.transform.localPosition.x, dirImg.transform.localPosition.y);
        speedText.text = $"速度：" + sendSpeedValue.ToString();
        // 为方向盘添加事件
        var dirTrigger = dirImg.GetComponent<EventTrigger>();
        AddTriggerEvent(dirTrigger, EventTriggerType.BeginDrag, OnDirBeginDrag);
        AddTriggerEvent(dirTrigger, EventTriggerType.Drag, OnDirDrag);
        AddTriggerEvent(dirTrigger, EventTriggerType.EndDrag, OnDirEndDrag);
        // 为速度盘添加事件
        var speedTrigger = speedImg.GetComponent<EventTrigger>();
        AddTriggerEvent(speedTrigger, EventTriggerType.BeginDrag, OnSpeedBeginDrag);
        AddTriggerEvent(speedTrigger, EventTriggerType.Drag, OnSpeedDrag);
        AddTriggerEvent(speedTrigger, EventTriggerType.EndDrag, OnSpeedEndDrag);

        // 启动连接判断定时器
        timerCoroutine = StartCoroutine(StartTimer(0.5f));

        // 读取历史连接地址
        configPath = Application.persistentDataPath + "/ip.txt";
        if (File.Exists(configPath))
        {
            string fileContent = File.ReadAllText(configPath);
            if (!string.IsNullOrEmpty(fileContent) && IPAddress.TryParse(fileContent, out IPAddress ipAddress))
            {
                // 自动连接网络
                StartConnect(ipAddress.ToString());
            }
        }
    }

    // 为EventTrigger添加事件
    private void AddTriggerEvent(EventTrigger dstTrigger, EventTriggerType eventID, UnityAction<BaseEventData> callback)
    {
        EventTrigger.Entry clickEntry = new EventTrigger.Entry();
        clickEntry.eventID = eventID;
        clickEntry.callback.AddListener(callback);
        dstTrigger.triggers.Add(clickEntry);
    }

    // 网络检查定时器
    IEnumerator StartTimer(float interval)
    {
        while (true)
        {
            yield return new WaitForSeconds(interval);
            // 定时器触发后执行的代码
            heartCount += 1;
            if (udpClient != null)
            {
                if (heartCount > 4)
                {
                    udpClient.Close();
                    udpClient = null;
                    wifiImg.sprite = wifiOff;
                    Debug.Log($"Disconnect network because of time out");
                }
                // 发送移动事件，同时作为心跳使用
                SendCmdData("Move", sendDirValue.ToString() + "|" + sendSpeedValue.ToString());
            }
        }
    }

    // 开始连接网络
    private void StartConnect(string ipStr)
    {
        if (ipStr.Length < 8)
            return;
        Debug.Log($"Start connect {ipStr}");

        ipText.text = ipStr;
        wifiImg.sprite = wifiOff;
        if (udpClient != null)
        {
            udpClient.Close();
            udpClient = null;
        }
        udpClient = new UdpClient();
        udpClient.Connect(ipStr, dstPort);
        udpClient.BeginReceive(new AsyncCallback(OnReceived), udpClient);
        // 发送登录命令
        SendCmdData("Login");
        // 连接时迅速检测是否连接成功
        heartCount = 3;
    }

    // 发送指定命令
    private void SendCmdData(string typeName, string typeValue = null)
    {
        if (udpClient != null)
        {
            var dstDic = new Dictionary<string, string>() {{"Type",typeName}};
            if (typeValue != null)
            {
                dstDic["Value"] = typeValue;
            }
            byte[] data = Encoding.UTF8.GetBytes(Json.Encode(dstDic));
            udpClient.Send(data, data.Length);
        }
    }

    // 接收到的命令处理
    private void DealRecvCmd(Dictionary<string, string> cmdDic)
    {
        if (cmdDic.ContainsKey("Login"))
        {
            // 登陆成功数据包
            heartCount = 0;
            wifiImg.sprite = wifiOn;
        }
        else if (cmdDic.ContainsKey("Heart"))
        {
            // 心跳包
            heartCount = 0;
        }
    }

    void OnReceived(IAsyncResult result)
    {
        UdpClient socket = result.AsyncState as UdpClient;
        IPEndPoint source = new IPEndPoint(0, 0);
        byte[] message = socket.EndReceive(result, ref source);
        if (message[0] == '0')
        {
            // camera帧数据，也被认为是一种心跳包
            heartCount = 0;
            // 第x帧
            int frameIndex = message[1];
            if (!receivedSlices.ContainsKey(frameIndex))
            {
                receivedFrameQueue.Enqueue(frameIndex);
                receivedSlices.Add(frameIndex, new Dictionary<int, byte[]>());
                // 判断缓存的大小, 超出大小则清理
                if (receivedFrameQueue.Count > 4)
                {
                    int removeFrameIndex = receivedFrameQueue.Dequeue();
                    if (receivedSlices.ContainsKey(removeFrameIndex))
                        receivedSlices.Remove(removeFrameIndex);
                }
            }
            // 此帧总共x片
            int stepCount = (message[2]) << 8 | message[3];
            // 此帧当前x片
            int stepIndex = (message[4]) << 8 | message[5];
            byte[] sliceData = message.Skip(6).ToArray();
            receivedSlices[frameIndex][stepIndex] = sliceData;
            if (receivedSlices[frameIndex].Count >= stepCount)
            {
                // 按顺序重组数据
                byte[] reconstructedData = Enumerable.Range(0, receivedSlices[frameIndex].Count)
                    .SelectMany(i => receivedSlices[frameIndex][i])
                    .ToArray();
                Debug.Log($"OnReceived {frameIndex}, {stepCount}, {stepIndex}, {reconstructedData.Length}");
                
                File.WriteAllBytes(Application.persistentDataPath + "/cam.jpg", reconstructedData);
                Texture2D texture = new Texture2D(1024, 1024);
                Debug.Log($"texture ");
                if (texture.LoadImage(reconstructedData))
                {
                    Debug.Log($"texture1 {texture}, {texture.width}, {texture.height}");
                    // 将Texture2D设置给RawImage组件
                    frameImg.texture = texture;
                    // 重置显示大小
                    (frameImg.transform as RectTransform).sizeDelta = new Vector2(texture.width * Screen.height / texture.height, Screen.height);
                }
            }
        }
        else
        {
            // 控制命令数据
            string returnData = Encoding.UTF8.GetString(message);
            var retCmd = Json.Decode(returnData.Substring(1)) as Dictionary<string, string>;
            if (retCmd != null)
            {
                DealRecvCmd(retCmd);
            }
        }
        socket.BeginReceive(new AsyncCallback(OnReceived), socket);
    }

    private void OnDestroy()
    {
        if (udpClient != null)
        {
            udpClient.Close();
            udpClient = null;
        }
        if (timerCoroutine != null)
        {
            StopCoroutine(timerCoroutine);
            timerCoroutine = null;
        }
    }

    // Wifi按钮事件
    public void OnWifiClick()
    {
        if (udpClient == null)
        {
            StartConnect(ipText.text);
        }
    }

    // IP地址点击事件
    public void OnIPTextClick()
    {
        ipText.enabled = false;
        ipInput.text = ipText.text;
        ipInput.gameObject.SetActive(true);
    }

    // IP地址输入完成事件
    public void OnIPInputOver()
    {
        // 检查输入是否是正常的IP地址
        if (ipInput.gameObject.activeSelf && !string.IsNullOrEmpty(ipInput.text) && IPAddress.TryParse(ipInput.text, out IPAddress ipAddress))
        {
            // 保存新的连接地址
            File.WriteAllText(configPath, ipAddress.ToString());
            // 开始连接新地址
            StartConnect(ipAddress.ToString());

            // 隐藏输入框
            ipText.enabled = true;
            ipInput.gameObject.SetActive(false);
        }
    }
    ///////////////////////////////////////////////拖动事件///////////////////////////////////////////////
    // 方向开始拖动事件
    public void OnDirBeginDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        dirPointId = pointData.pointerId;
        UpdateDirPosition(pointData.position);
    }

    // 更新方向盘的显示位置
    private void UpdateDirPosition(Vector2 touchPosition)
    {
        // 将屏幕坐标转换为UI坐标
        Vector2 uiPos;
        RectTransformUtility.ScreenPointToLocalPointInRectangle(dirBgImg.transform as RectTransform, touchPosition, null, out uiPos);
        Vector2 moveDir = (uiPos - dirOrginPos);
        if (moveDir.sqrMagnitude > dirMoveDis * dirMoveDis)
        {
            dirImg.transform.localPosition = dirOrginPos + moveDir.normalized * dirMoveDis;
            SetDirAngle(moveDir);
        }
        else
        {
            dirImg.transform.localPosition = uiPos;
            // 大于一定范围才发送位置
            if (moveDir.sqrMagnitude > dirMoveDis * dirMoveDis * 0.25f)
            {
                SetDirAngle(moveDir);
            }
            else
            {
                // 取消位置事件发送
                SetDirAngle(Vector2.zero);
            }
        }
    }

    private void SetDirAngle(Vector2 dirV)
    {
        if (dirV.x < float.Epsilon && dirV.y < float.Epsilon )
        {
            sendDirValue = -1;
        }
        else
        {
            // 使用Atan2函数计算极坐标角度
            float angle = Mathf.Atan2(dirV.y, dirV.x) * Mathf.Rad2Deg;
            sendDirValue = (int)Mathf.Repeat(angle, 360f);
        }
    }
    
    // 方向拖动事件
    public void OnDirDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        if (dirPointId == pointData.pointerId)
        {
            UpdateDirPosition(pointData.position);
        }
    }
    
    // 方向结束拖动事件
    public void OnDirEndDrag(BaseEventData eventData)
    {
        dirImg.transform.localPosition = dirOrginPos;
        dirPointId = -1;
    }

    // 速度拖动事件
    public void OnSpeedBeginDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        speedPointId = pointData.pointerId;
        UpdateSpeedPosition(pointData.position);
    }

    // 更新速度的显示位置
    private void UpdateSpeedPosition(Vector2 touchPosition)
    {
        // 将屏幕坐标转换为UI坐标
        Vector2 uiPos;
        var speedBgTransform = speedBgImg.transform as RectTransform;
        RectTransformUtility.ScreenPointToLocalPointInRectangle(speedBgTransform, touchPosition, null, out uiPos);
        // 限制拖动的范围
        float speedImgLength = (speedImg.transform as RectTransform).sizeDelta.y;
        float maxMoveLength = speedBgTransform.sizeDelta.y - speedImgLength;
        var curScrollHeight = uiPos.y + maxMoveLength * 0.5f;
        if (curScrollHeight >= 0 && curScrollHeight <= maxMoveLength)
        {
            // 拖动距离划分成10等分，计算当前的速度
            speedImg.transform.localPosition = new Vector3(speedImg.transform.localPosition.x, uiPos.y, 0);
            sendSpeedValue = (int)((curScrollHeight + speedImgLength * 0.5f) * 9 / maxMoveLength) + 1;
            speedText.text = $"速度：" + sendSpeedValue.ToString();
        }
    }

    // 速度拖动事件
    public void OnSpeedDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        if (speedPointId == pointData.pointerId)
        {
            UpdateSpeedPosition(pointData.position);
        }
    }

    //  速度拖动完成事件
    public void OnSpeedEndDrag(BaseEventData eventData)
    {
        speedPointId = -1;
    }
}