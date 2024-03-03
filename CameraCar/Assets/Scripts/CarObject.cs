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
    #region 私有变量
    private string      configPath;
    private UdpClient   udpClient = null;
    private int         dstPort = 7890;
    private int         heartCount = 0;//心跳
    private Coroutine   timerCoroutine = null;// 网络连接检查器
    
    private Vector2     dirOrginPos;        // 方向键的原始位置
    private const float dirMoveDis = 75;    // 方向键移动的最大距离
    private int         dirPointId = -1;
    private int         speedPointId = -1;
    private int         rotatePointId = -1;
    private int         sendDirValue = -1;  // 移动的方向值
    private int         sendSpeedValue = 6; // 移动的速度值
    private Vector2     lastRotatePos = Vector2.zero;   // 云台上次滑动的位置
    private float       rotateMoveDis = 0;  // 云台上次滑动的距离

    private byte[]      recvedBytes = null; // 网络数据缓存
    private object      recvLockObj = new object();
    private bool        takePhotoOnce = false;  // 是否拍照
    private float       noticeUpdateTime = 0;   // 提示文本更新时间
    private float       battleUpdateTime = 0;   // 电池更新时间
    private float       fpsUpdateTime = 0;      // FPS计算更新时间
    private int         fpsCount = 0;           // FPS值
    private bool        lightState = false;     // 电筒是否亮
    private float       camMoveRotate = 0;      // 当前云台位置，0表示正对位置
    #endregion

    #region 绑定结点
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
    public Text         fpsText;    // 摄像机FPS文本
    public GameObject   photoObj;   // 拍照按钮对象
    public Text         noticeText; // 提示文本
    public SlicedFilledImage batteryImg;    // 电量显示图
    public Image        lightImg;   // 电筒指示图
    public GameObject   rotateCenterObj;    // 摄像机云台居中按钮
    // 按钮状态图
    public Sprite       wifiOff;    // wifi已连接状态图
    public Sprite       wifiOn;     // wifi未连接状态图
    #endregion

    // udp接收到的数据
    Dictionary<int, Dictionary<int, byte[]>> receivedSlices = new Dictionary<int, Dictionary<int, byte[]>>();
    Queue<int> receivedFrameQueue = new Queue<int>();
    #region 处理方法
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
        // 为云台添加事件
        var rotateTrigger = frameImg.GetComponent<EventTrigger>();
        AddTriggerEvent(rotateTrigger, EventTriggerType.BeginDrag, OnRotateBeginDrag);
        AddTriggerEvent(rotateTrigger, EventTriggerType.Drag, OnRotateDrag);
        AddTriggerEvent(rotateTrigger, EventTriggerType.EndDrag, OnRotateEndDrag);

        // 启动连接判断定时器
        timerCoroutine = StartCoroutine(StartNetCheckTimer(0.1f));

        // 初始不可用拍照功能
        SetCameraEnabled(false);
        // 读取历史连接地址
        var initIpAddr = ipText.text;
        configPath = Application.persistentDataPath + "/ip.txt";
        if (File.Exists(configPath))
        {
            string fileContent = File.ReadAllText(configPath);
            if (!string.IsNullOrEmpty(fileContent) && IPAddress.TryParse(fileContent, out IPAddress ipAddress))
            {
                initIpAddr = ipAddress.ToString();
            }
        }
        // 自动连接网络
        StartConnect(initIpAddr);
        // 限制帧率
        Application.targetFrameRate = 30;
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
    IEnumerator StartNetCheckTimer(float interval)
    {
        while (true)
        {
            yield return new WaitForSeconds(interval);
            // 定时器触发后执行的代码
            heartCount += 1;
            if (udpClient != null)
            {
                if (heartCount > 20)
                {
                    // 关闭网络连接，并不发送Logout
                    DisconnectCar("Disconnect network because of time out", false);
                    continue;
                }
                // 发送移动事件，同时作为心跳使用
                SendCmdData("Move", sendDirValue.ToString() + "|" + sendSpeedValue.ToString());
                // 判断是否需要获取电池的信息
                if ((Time.realtimeSinceStartup - battleUpdateTime) > 10)
                {
                    SendCmdData("Battery");
                    battleUpdateTime = Time.realtimeSinceStartup;
                }
            }
            // 检查提示文本是否需要超时关闭
            if (noticeText.gameObject.activeSelf && (Time.realtimeSinceStartup - noticeUpdateTime) > 5)
                noticeText.gameObject.SetActive(false);

            // 处理云台的旋转
            if (Mathf.Abs(rotateMoveDis) > float.Epsilon)
            {
                // 转换到当前分辨率的距离
                var moveDis = rotateMoveDis * 720.0f / Screen.height;
                // 按移动360对应90度来计算最终位置
                camMoveRotate = camMoveRotate + (int)(moveDis * 0.25f);
                // 限制最大和最小值
                camMoveRotate = Math.Clamp(camMoveRotate, -60, 60);
                // 发送当前位置
                SendCmdData("Rotate", camMoveRotate.ToString());
                rotateMoveDis = 0;
                // 界面显示当前的旋转方向
                ShowNoticeText("Camera rotate to " + camMoveRotate.ToString());
            }
        }
    }

    // 设置Camera是否可用
    private void SetCameraEnabled(bool enabled)
    {
        // Debug.Log($"set camera to {enabled}");
        frameImg.gameObject.SetActive(enabled);
        photoObj.SetActive(enabled);
        rotateCenterObj.SetActive(enabled);
        // FPS文本显示
        fpsText.gameObject.SetActive(enabled);
        // 启动摄像机时更新一次FPS
        if (enabled)
        {
            fpsCount = 0;
            fpsText.text = $"FPS:0";
            fpsUpdateTime = Time.realtimeSinceStartup;
        }
    }

    // 设置电筒是否明亮
    private void SetLightOn(bool isOn)
    {
        // Debug.Log($"set light to {isOn}");
        lightState = isOn;
        lightImg.color = isOn ? new Color(0.34f, 0.46f, 1.0f) : new Color(0.611f, 0.611f, 0.611f);
        // 发送命令
        SendCmdData("Light", isOn ? "On" : "Down");
    }

    // 开始连接网络
    private void StartConnect(string ipStr)
    {
        if (ipStr.Length < 8)
            return;
        ShowNoticeText($"Start connect {ipStr}");

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
        // 重置电量检测倒计时
        battleUpdateTime = Time.realtimeSinceStartup;
        // 连接时迅速检测是否连接成功
        heartCount = 3;
    }

    // 发送指定命令
    private void SendCmdData(string typeName, string typeValue = null)
    {
        if (udpClient != null)
        {
            try
            {
                var dstDic = new Dictionary<string, string>() { { "Type", typeName } };
                if (typeValue != null)
                {
                    dstDic["Value"] = typeValue;
                }
                byte[] data = Encoding.UTF8.GetBytes(Json.Encode(dstDic));
                udpClient.Send(data, data.Length);
                // Debug.Log($"Send message : {typeName}|{typeValue}");
            }
            catch (Exception)
            {
                Debug.Log($"Send message : {typeName}|{typeValue} failed");
            }
        }
    }

    // 接收到的命令处理
    private void DealRecvCmd(Dictionary<string, object> cmdDic)
    {
        var typeCmd = cmdDic["Type"] as string;
        if (typeCmd == "Login")
        {
            // 登陆成功数据包
            // 设置wifi显示正常
            wifiImg.sprite = wifiOn;
            var esp_id = cmdDic["Value"] as string;
            // 判断拍照功能是否可用, ESP32-C3以T2开头
            SetCameraEnabled(!esp_id.StartsWith("T2"));
            ShowNoticeText($"Connect network {esp_id} success");
            // 登录后获取一次电池信息
            SendCmdData("Battery");
            batteryImg.fillAmount = 0;
            // 登录后重置云台位置
            OnRotateCenter();
            // 设置灯光状态
            SetLightOn(lightState);
        }
        else if (typeCmd == "Battery")
        {
            // 更新电池信息
            var battery_value = cmdDic["Value"] as string;
            if (int.TryParse(battery_value, out int result))
            {
                batteryImg.fillAmount = result * 0.01f;
            }
        }
        //else if (typeCmd == "Heart")
        //{
        //    // 心跳包
        //}
    }

    void OnReceived(IAsyncResult result)
    {
        if (udpClient == null)
        {
            return;
        }

        try
        {
            UdpClient socket = result.AsyncState as UdpClient;
            IPEndPoint source = new IPEndPoint(0, 0);
            byte[] message = socket.EndReceive(result, ref source);
            lock (recvLockObj)
            {
                // 判断一下recvedBytes，保证Login能被执行
                if (recvedBytes == null && message != null && message.Length > 1)
                {
                    recvedBytes = message;
                }
            }
            // 接收到数据，计数重置
            heartCount = 0;
            // 继续接收数据
            socket.BeginReceive(new AsyncCallback(OnReceived), socket);
        }
        catch (Exception)
        {
            Debug.Log("Recv message failed");
        }
    }

    private void Update()
    {
        // 处理UDP收到的数据
        if (recvedBytes != null)
        {
            lock(recvLockObj)
            {
                if (recvedBytes[0] == '0')
                {
                    // 第xCamera帧数据
                    int frameIndex = recvedBytes[1];
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
                    int stepCount = (recvedBytes[2]) << 8 | recvedBytes[3];
                    // 此帧当前x片
                    int stepIndex = (recvedBytes[4]) << 8 | recvedBytes[5];
                    byte[] sliceData = recvedBytes.Skip(6).ToArray();
                    receivedSlices[frameIndex][stepIndex] = sliceData;
                    if (receivedSlices[frameIndex].Count >= stepCount)
                    {
                        // 按顺序重组数据并保存，仅主线程中才能重置Texture
                        var cameraBytes = Enumerable.Range(0, receivedSlices[frameIndex].Count)
                            .SelectMany(i => receivedSlices[frameIndex][i])
                            .ToArray();
                        SetCameraBytes(cameraBytes);
                        // Debug.Log($"OnReceived {frameIndex}, {stepCount}, {stepIndex}, {cameraBytes.Length}");
                    }
                }
                else
                {
                    // 控制命令数据
                    string commandData = Encoding.UTF8.GetString(recvedBytes.Skip(1).ToArray());
                    // Debug.Log($"OnReceived cammand {commandData}");
                    var retCmd = Json.Decode(commandData) as Dictionary<string, object>;
                    if (retCmd != null)
                    {
                        DealRecvCmd(retCmd);
                    }
                }
                // 数据处理后，置空
                recvedBytes = null;
            }
        }
        
        // 退出应用
        if (Application.platform == RuntimePlatform.Android)
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                Application.Quit();
            }
        }
    }

    // 显示摄像头数据
    private void SetCameraBytes(byte[] cameraBytes)
    {
        // Camera数据主线程中重置
        if (cameraBytes != null)
        {
            Texture2D texture = new Texture2D(32, 32);
            if (texture.LoadImage(cameraBytes))
            {
                // 将原Texture删除，避免内存膨胀
                if (frameImg.texture)
                {
                    Destroy(frameImg.texture);
                }
                // Debug.Log($"texture1 {texture}, {texture.width}, {texture.height}");
                // 将Texture2D设置给RawImage组件
                frameImg.texture = texture;
                // 重置显示大小
                (frameImg.transform as RectTransform).sizeDelta = new Vector2(texture.width * 720 / texture.height, 720);
            }
            else
            {
                // 删除刚创建的Texture
                Destroy(texture);
            }
            // 将图片保存下载
            if (takePhotoOnce)
            {
                // 以当前时间作用文件名
                var photoName = "Car_" + DateTime.Now.ToString("HH_mm_ss_fff") + ".png";
                var retPermission = NativeGallery.SaveImageToGallery(cameraBytes, "Camera-Car", photoName, (bool success, string path) =>
                {
                    if (success)
                    {
                        ShowNoticeText($"Save photo to {photoName}");
                    }
                });
                if (retPermission == NativeGallery.Permission.Denied)
                {
                    ShowNoticeText("No save photo permission");
                }
                takePhotoOnce = false;
            }
            // FPS计算更新
            fpsCount += 1;
            if ((Time.realtimeSinceStartup - fpsUpdateTime) > 1)
            {
                fpsText.text = $"FPS:{fpsCount}";
                fpsCount = 0;
                fpsUpdateTime = Time.realtimeSinceStartup;
            }
        }
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

    // 应用后台切换事件
    private void OnApplicationPause(bool pauseStatus)
    {
        if (pauseStatus)
        {
            // 后台时断开连接
            DisconnectCar("Disconnect network by application pause", true);
        }
        else if (timerCoroutine != null)
        {
            // 切换到前台时，重新连接
            StartConnect(ipText.text);
        }
    }

    // Wifi按钮事件
    public void OnWifiClick()
    {
        // 网络连接或断开连接进行切换
        if (udpClient == null)
        {
            StartConnect(ipText.text);
        }
        else
        {
            DisconnectCar("Disconnect network by hand", true);
        }
    }

    // 拍照按钮事件
    public void OnTakePhoto()
    {
        // 标记拍照一次，具体保存在Update中执行
        takePhotoOnce = true;
    }

    // 灯光按钮事件
    public void OnLightAction()
    {
        SetLightOn(!lightState);
    }

    // 居中事件
    public void OnRotateCenter()
    {
        camMoveRotate = 0;
        SendCmdData("Rotate", camMoveRotate.ToString());
    }

    // 主动断开网络连接
    private void DisconnectCar(string logStr, bool logout)
    {
        if (udpClient != null)
        {
            // 先发送Logout，再关闭socket
            if (logout)
                SendCmdData("Logout");
            udpClient.Close();
            udpClient = null;
            wifiImg.sprite = wifiOff;
            // 不可用拍照功能
            SetCameraEnabled(false);
            ShowNoticeText(logStr);
        }
    }

    // 显示日志
    private void ShowNoticeText(string notice)
    {
        // 更新日志显示时间
        noticeUpdateTime = Time.realtimeSinceStartup;
        noticeText.gameObject.SetActive(true);
        noticeText.text = notice;
        Debug.Log(notice);
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
    #endregion

    #region 移动拖动盘
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
        if (Mathf.Abs(dirV.x) < float.Epsilon && Mathf.Abs(dirV.y) < float.Epsilon )
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
        // 取消位置事件发送
        SetDirAngle(Vector2.zero);
    }
    #endregion

    #region 调速拖动事件
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
    #endregion

    #region 云台旋转事件
    // 旋转拖动事件
    public void OnRotateBeginDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        rotatePointId = pointData.pointerId;
        // 记录当前位置
        lastRotatePos = pointData.position;
    }

    // 旋转拖动事件
    public void OnRotateDrag(BaseEventData eventData)
    {
        var pointData = (eventData as PointerEventData);
        if (rotatePointId == pointData.pointerId)
        {
            rotateMoveDis = pointData.position.x - lastRotatePos.x;
        }
    }

    // 旋转拖动完成事件
    public void OnRotateEndDrag(BaseEventData eventData)
    {
        rotatePointId = -1;
    }
    #endregion
}