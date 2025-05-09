## 程序运行说明

### 1. 环境准备

*   **Python**: 确保已安装 Python 3.9 版本。
*   **pip**: 确保已安装 pip 包管理器。
*   **MySQL**: 确保已安装并运行 MySQL 数据库服务。

### 2. 安装依赖

克隆或下载项目代码到本地。在项目根目录下打开终端，运行以下命令安装所需的 Python 库：

```bash
pip install -r requirements.txt
```

### 3. 数据库配置与初始化

*   **配置连接**: 打开 `models.py` 文件，根据您的 MySQL 安装情况修改以下数据库连接信息：
    ```python
    host = '127.0.0.1'  # MySQL 服务器地址
    user = 'root'      # MySQL 用户名
    password = ''      # MySQL 密码 (如果设置了密码，请填写)
    database = 'xinxi' # 要使用的数据库名称
    ```
*   **创建数据库**: 在 MySQL 中手动创建名为 `xinxi` (或您在 `models.py` 中指定的名称) 的数据库。
*   **初始化表和角色**: 在项目根目录下运行 `models.py` 脚本来创建数据库表结构，并初始化管理员角色和用户：
    ```bash
    python models.py
    ```
    您应该会看到类似 "数据库检查与初始化完成。" 的输出。

### 4. 运行主应用程序

数据库准备就绪后，运行主应用程序：

```bash
python main.py
```

应用程序默认会在 `http://0.0.0.0:8080` 或 `http://127.0.0.1:8080` 上启动。您可以在浏览器中访问此地址。

### 5. (可选) 运行模型训练/测试脚本

如果您需要重新训练模型或使用保存的模型进行批量预测评估，可以运行：

```bash
python test_model.py
```

该脚本会连接数据库（或使用 CSV 备份），处理数据，训练或加载模型，并输出评估结果。确保运行此脚本前 `simple_model.pkl` 模型文件存在（如果只是测试加载和预测），或者有足够的数据用于训练。

# 雷达图悬停提示实现说明 (`templates/visualization.html`)

本文档解释了"各地区平均分数线"雷达图（ID: `chart6`）如何在用户鼠标悬停时显示具体数据。

## 核心实现

悬停提示功能主要通过 ECharts 的 `tooltip` 配置和 `mousemove` 事件监听器结合实现。

### 1. Tooltip 配置

我们为雷达图配置了 `tooltip`，使其在鼠标悬停到图表项时触发。

```javascript
{
    // ... 其他配置 ...
    tooltip: {
        trigger: 'item', // 触发类型设置为 'item'，当鼠标悬停到数据项时触发
        formatter: function(params) {
            // 这个 formatter 函数用于自定义提示框显示的内容
            // 由于我们希望通过 mousemove 事件更精确地控制提示，
            // 所以这里的逻辑相对简单，主要处理非总体数据系列的情况。
            if (params.seriesIndex === 0) {
                // 对于总体数据系列（背景区域），我们依赖 mousemove 事件来显示提示。
                // 可以返回空字符串或稍后由 mousemove 动态设置。
                return '';
            } else {
                // 对于代表单个地区的点（虽然在这个实现中它们不直接显示），
                // 我们可以直接返回该地区的数据。
                var idx = params.seriesIndex - 1;
                if (idx >= 0 && idx < chartData.region_avg_score_list.length) {
                    return chartData.region_avg_score_list[idx] + ': ' + chartData.region_avg_score_count[idx];
                }
                return '';
            }
        }
    },
    // ... 其他配置 ...
}
```

**关键点**：
*   `trigger: 'item'`：指定当鼠标悬停在数据项（如图中的点或区域）上时触发提示。
*   `formatter`: 允许我们自定义提示框的内容。在这个实现中，`formatter` 本身并不直接用于显示雷达图区域的悬停数据，主要逻辑放到了 `mousemove` 事件中。

### 2. Mousemove 事件监听器

为了在鼠标悬停到雷达图的不同 *区域* 时显示对应地区的数据，我们添加了一个 `mousemove` 事件监听器。这个监听器会计算鼠标指针当前所在的区域，并动态地显示该区域对应地区的名称和数据。

```javascript
chart6.on('mousemove', function(params) {
    // params.event 包含鼠标事件的详细信息，如 offsetX, offsetY
    var coord = params.event;

    // 获取图表实例和容器的尺寸，用于计算角度
    var chartInstance = params.chart;
    var cx = chartInstance.getWidth() / 2;  // 雷达图中心 x 坐标
    var cy = chartInstance.getHeight() / 2; // 雷达图中心 y 坐标

    // 计算鼠标相对于雷达图中心的角度 (弧度转角度)
    var angle = Math.atan2(coord.offsetY - cy, coord.offsetX - cx);
    angle = (angle * 180 / Math.PI + 360) % 360; // 转换为 0-360 度

    // 获取雷达图指示器（地区列表）的数量
    var count = chartData.region_avg_score_list.length;
    // 根据角度计算当前鼠标所在的指示器（区域）索引
    // 每个区域大约占据 360 / count 度
    var index = Math.floor((angle + (360/count/2)) % 360 / (360 / count)); // 加偏移量使区域划分更准确

    // 高亮当前区域（视觉反馈，可选）
    // ECharts 5+ 可能不支持直接高亮雷达图区域，此部分可能需要调整或移除
    // for (var i = 0; i < chartData.region_avg_score_list.length; i++) {
    //     chartInstance.dispatchAction({
    //         type: i === index ? 'highlight' : 'downplay',
    //         seriesIndex: 0, // 针对第一个系列（背景区域）
    //         dataIndex: 0
    //     });
    // }

    // 动态显示 ECharts 提示框 (Tooltip)
    if (index >= 0 && index < chartData.region_avg_score_list.length) {
        chartInstance.dispatchAction({
            type: 'showTip', // 触发显示提示框的操作
            seriesIndex: 0,   // 在哪个系列上显示（通常是第一个）
            dataIndex: 0,     // 对应的数据索引（通常是第一个）
            position: [coord.offsetX + 10, coord.offsetY + 10], // 提示框显示位置，稍微偏离鼠标
            // 关键：动态设置提示框的内容
            formatter: chartData.region_avg_score_list[index] + ': ' + chartData.region_avg_score_count[index]
        });
    }
});

// 添加 mouseout 事件，当鼠标移出图表时隐藏提示框
chart6.on('mouseout', function(params) {
    params.chart.dispatchAction({ type: 'hideTip' });
});
```

**关键点**：
*   `chart6.on('mousemove', ...)`：监听指定 ECharts 实例上的鼠标移动事件。
*   **角度计算**：通过 `Math.atan2` 计算鼠标位置相对于图表中心的角度。
*   **区域索引计算**：根据角度和指示器的数量，确定鼠标当前悬停在哪个地区对应的扇区。
*   `chartInstance.dispatchAction({ type: 'showTip', ... })`：这是核心！我们手动触发 ECharts 显示提示框的操作。
*   **动态 `formatter`**：在 `dispatchAction` 中直接提供 `formatter` 字符串，内容是根据计算出的 `index` 动态生成的地区名称和数据。
*   `chart6.on('mouseout', ...)`：监听鼠标移出事件，并触发 `hideTip` 动作来隐藏提示框。

## 预测表单下拉框联动实现 (`templates/predict.html` & `main.py`)

本文档解释了预测表单中地区、部门名称、职位和专业下拉框如何实现联动效果，即根据前一个下拉框的选择来动态更新后一个下拉框的选项。

### 核心实现

联动效果主要通过以下几个部分协同工作：

1.  **HTML Select 元素**: 在 `templates/predict.html` 中定义下拉框元素。
2.  **JavaScript 事件监听**: 使用 JavaScript 监听下拉框的 `change` 事件。
3.  **Flask API 端点**: 在 `main.py` 中定义 API 端点，根据传入的参数从数据库查询并返回过滤后的选项列表。
4.  **JavaScript 数据请求与更新**: 当下拉框选项改变时，JavaScript 向对应的 Flask API 发送请求，获取新的选项列表，并更新下一个下拉框的内容。

### 1. HTML 结构 (`templates/predict.html`)

每个下拉框都有一个唯一的 ID，方便 JavaScript 操作。

```html
<!-- 地区 -->
<div class="form-group">
    <label for="region">地区</label>
    <select class="form-control" id="region" name="region">
        <option value="">-- 请选择地区 --</option>
        {% for region in regions %}
            <option value="{{ region }}">{{ region }}</option>
        {% endfor %}
    </select>
</div>

<!-- 部门名称 -->
<div class="form-group">
    <label for="department">部门名称</label>
    <select class="form-control" id="department" name="department" disabled>
        <option value="">-- 请先选择地区 --</option>
    </select>
</div>

<!-- 职位 -->
<div class="form-group">
    <label for="position">职位</label>
    <select class="form-control" id="position" name="position" disabled>
        <option value="">-- 请先选择部门 --</option>
    </select>
</div>

<!-- 专业 -->
<div class="form-group">
    <label for="major">专业</label>
    <select class="form-control" id="major" name="major" disabled>
        <option value="">-- 请先选择职位 --</option>
    </select>
</div>
```

**关键点**: 
*   后续的下拉框（部门、职位、专业）初始状态是 `disabled`，并在没有前置选项时显示提示信息。

### 2. Flask API 端点 (`main.py`)

定义了三个 API 端点来提供过滤后的数据：

*   `/api/get_departments`: 根据选择的 `region` 返回对应的部门列表。
*   `/api/get_positions`: 根据选择的 `region` 和 `department` 返回对应的职位列表。
*   `/api/get_majors`: 根据选择的 `region`、`department` 和 `position` 返回对应的专业列表。

```python
@app.route('/api/get_departments', methods=['GET'])
def get_departments():
    """根据地区获取部门列表"""
    region = request.args.get('region', '')
    if not region:
        return jsonify([])
    df = load_data_from_db() # 注意：频繁加载可能影响性能，可考虑缓存
    filtered_df = df[df['地区'] == region]
    departments = filtered_df['部门名称'].unique().tolist()
    return jsonify(departments)

@app.route('/api/get_positions', methods=['GET'])
def get_positions():
    """根据地区和部门获取职位列表"""
    region = request.args.get('region', '')
    department = request.args.get('department', '')
    if not region or not department:
        return jsonify([])
    df = load_data_from_db()
    filtered_df = df[(df['地区'] == region) & (df['部门名称'] == department)]
    positions = filtered_df['职位'].unique().tolist()
    return jsonify(positions)

@app.route('/api/get_majors', methods=['GET'])
def get_majors():
    """根据地区、部门和职位获取专业列表"""
    region = request.args.get('region', '')
    department = request.args.get('department', '')
    position = request.args.get('position', '')
    if not region or not department or not position:
        return jsonify([])
    df = load_data_from_db()
    filtered_df = df[(df['地区'] == region) & 
                    (df['部门名称'] == department) & 
                    (df['职位'] == position)]
    majors = filtered_df['专业'].unique().tolist()
    return jsonify(majors)
```

**关键点**: 
*   API 端点接收 GET 请求参数。
*   从数据库加载数据并根据参数进行过滤。
*   返回 JSON 格式的选项列表。
*   **性能注意**: 当前实现每次 API 调用都会重新加载数据 (`load_data_from_db()`)，在高并发场景下可能需要进一步优化（如使用缓存）。

### 3. JavaScript 事件处理与更新 (`templates/predict.html`)

使用 JavaScript 监听 `change` 事件，并在事件触发时执行更新逻辑。

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const regionSelect = document.getElementById('region');
    const departmentSelect = document.getElementById('department');
    const positionSelect = document.getElementById('position');
    const majorSelect = document.getElementById('major');

    // 更新下拉框选项的辅助函数
    function updateSelectOptions(selectElement, options, placeholder) {
        selectElement.innerHTML = ''; // 清空现有选项
        const placeholderOption = document.createElement('option');
        placeholderOption.value = '';
        placeholderOption.textContent = placeholder;
        selectElement.appendChild(placeholderOption);

        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            selectElement.appendChild(opt);
        });
        selectElement.disabled = false; // 启用下拉框
    }

    // 重置并禁用后续下拉框
    function resetDependentSelects(startLevel) {
        if (startLevel <= 1) {
            departmentSelect.innerHTML = '<option value="">-- 请先选择地区 --</option>';
            departmentSelect.disabled = true;
        }
        if (startLevel <= 2) {
            positionSelect.innerHTML = '<option value="">-- 请先选择部门 --</option>';
            positionSelect.disabled = true;
        }
        if (startLevel <= 3) {
            majorSelect.innerHTML = '<option value="">-- 请先选择职位 --</option>';
            majorSelect.disabled = true;
        }
    }

    // 监听地区选择变化
    regionSelect.addEventListener('change', function() {
        const selectedRegion = this.value;
        resetDependentSelects(1);
        if (selectedRegion) {
            fetch(`/api/get_departments?region=${encodeURIComponent(selectedRegion)}`)
                .then(response => response.json())
                .then(data => {
                    updateSelectOptions(departmentSelect, data, '-- 请选择部门 --');
                })
                .catch(error => console.error('Error fetching departments:', error));
        }
    });

    // 监听部门选择变化
    departmentSelect.addEventListener('change', function() {
        const selectedRegion = regionSelect.value;
        const selectedDepartment = this.value;
        resetDependentSelects(2);
        if (selectedDepartment) {
            fetch(`/api/get_positions?region=${encodeURIComponent(selectedRegion)}&department=${encodeURIComponent(selectedDepartment)}`)
                .then(response => response.json())
                .then(data => {
                    updateSelectOptions(positionSelect, data, '-- 请选择职位 --');
                })
                .catch(error => console.error('Error fetching positions:', error));
        }
    });

    // 监听职位选择变化
    positionSelect.addEventListener('change', function() {
        const selectedRegion = regionSelect.value;
        const selectedDepartment = departmentSelect.value;
        const selectedPosition = this.value;
        resetDependentSelects(3);
        if (selectedPosition) {
            fetch(`/api/get_majors?region=${encodeURIComponent(selectedRegion)}&department=${encodeURIComponent(selectedDepartment)}&position=${encodeURIComponent(selectedPosition)}`)
                .then(response => response.json())
                .then(data => {
                    updateSelectOptions(majorSelect, data, '-- 请选择专业 --');
                })
                .catch(error => console.error('Error fetching majors:', error));
        }
    });
});
```

**关键点**:
*   `DOMContentLoaded`: 确保在 DOM 加载完毕后执行脚本。
*   获取各个 `select` 元素的引用。
*   `updateSelectOptions`: 封装了清空、添加占位符、填充新选项和启用下拉框的逻辑。
*   `resetDependentSelects`: 当上级下拉框改变时，重置并禁用所有后续的下拉框。
*   `addEventListener('change', ...)`: 为每个相关的下拉框（地区、部门、职位）添加事件监听器。
*   `fetch`: 使用 Fetch API 向 Flask 后端发送异步请求。
*   `encodeURIComponent`: 对 URL 参数进行编码，防止特殊字符引起问题。
*   `.then()`: 处理 API 返回的 JSON 数据，并调用 `updateSelectOptions` 更新界面。
*   `.catch()`: 处理请求过程中可能出现的错误。

### 总结

预测表单的下拉框联动是通过前端 JavaScript 监听用户选择，然后向后端 Flask API 请求过滤后的数据，最后再由 JavaScript 更新后续下拉框选项来实现的。这种前后端分离的方式使得逻辑清晰，易于维护。

## 总结

通过结合 `tooltip` 的基本配置和 `mousemove` 事件监听器，我们实现了在雷达图上悬停时，能够根据鼠标所在的精确区域动态显示对应地区数据的交互效果。`mousemove` 事件处理函数负责计算当前区域并动态生成提示内容，然后通过 `dispatchAction` 来控制提示框的显示。

## 简单 Flask 测试应用说明 (`simple_app.py`)

`simple_app.py` 文件包含一个非常基础的 Flask 应用实例。这个应用的主要目的是提供一个简单的环境来测试 Flask 本身或某些基本功能是否正常工作，例如路由和模板渲染。

### 应用代码

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # 定义根路由 ('/')
    # 当用户访问应用的根 URL 时，返回一个简单的字符串
    return "简单的 Flask 测试应用正常运行！"

@app.route('/template')
def template():
    # 定义 '/template' 路由
    # 当用户访问 '/template' URL 时，尝试渲染名为 'test.html' 的模板文件
    # 注意：这需要项目目录下存在一个名为 'templates' 的文件夹，
    # 并且该文件夹内有一个 'test.html' 文件。
    return render_template('test.html')

if __name__ == '__main__':
    # 当直接运行此脚本时，启动 Flask 开发服务器
    # debug=True: 启用调试模式，代码更改后服务器会自动重启，并提供更详细的错误信息
    # host='0.0.0.0': 使服务器可以从本地网络中的任何 IP 地址访问
    # port=8081: 指定服务器监听的端口号为 8081 (区别于主应用的 8080)
    app.run(debug=True, host='0.0.0.0', port=8081) 
```

### 主要功能

1.  **根路由 (`/`)**: 访问应用的根路径（例如 `http://localhost:8081/`）会返回一个简单的文本消息，确认应用正在运行。
2.  **模板路由 (`/template`)**: 访问 `/template` 路径（例如 `http://localhost:8081/template`）会尝试加载并渲染 `templates/test.html` 文件。这可以用来测试 Flask 的模板渲染功能。

### 启动方式

可以直接通过 Python 运行此文件来启动这个测试服务器：

```bash
python simple_app.py
```

服务器将在端口 8081 上启动，与主应用（可能运行在 8080 端口）分开。

### 用途

这个简单的应用通常用于：
*   快速验证 Flask 环境是否配置正确。
*   测试基本的路由定义和请求处理。
*   测试模板引擎 (`render_template`) 的功能。
*   作为一个最小化的示例，用于教学或演示 Flask 的基本概念。

它与项目中的主应用 (`main.py`) 是独立的，运行在不同的端口上。 

## 预测模型说明 (`simple_model.pkl` & `main.py`)

`simple_model.pkl` 文件是一个序列化的 Python 对象文件，通常用于存储训练好的机器学习模型及其相关数据。在这个项目中，它存储了用于预测分数线的模型。

### 模型类型与用途

根据 `main.py` 中 `/predict` 路由的代码，该文件包含一个使用 **LightGBM** 框架训练的模型。LightGBM 是一种高效的梯度提升决策树算法，常用于分类和回归任务。

在这个应用中，该模型的主要用途是根据用户输入的特征（如地区、部门、职位、学历、专业、招考人数、报考人数、年份等）来**预测相应的分数线**。

### 加载与使用 (`main.py`)

模型通过 Python 的 `pickle` 库加载到应用中。

```python
import pickle
import pandas as pd

# ... (在 /predict 路由中) ...

try:
    # 加载 pickle 格式的模型文件
    model_path = 'simple_model.pkl'
    print(f"尝试加载模型: {model_path}")
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    # 从加载的数据中提取模型和元数据
    model = model_data['model']          # LightGBM 模型对象
    encoders = model_data['encoders']    # 用于分类特征编码的 LabelEncoders
    scaler = model_data['scaler']        # 用于数值特征标准化的 StandardScaler
    features = model_data['features']    # 模型训练时使用的特征列表
    metrics = model_data['metrics']      # 模型评估指标 (例如 R^2, RMSE, 置信度)
    
    print(f"成功加载 {model_data.get('model_name', 'LightGBM')} 模型，特征数量: {len(features)}")
    
    # ... 准备预测数据 (pred_data) ...
    
    # 特征编码 (处理分类变量)
    for col, encoder in encoders.items():
        if col in pred_data.columns:
            # ... (处理已知和未知类别) ...
            pred_data[col+'_encoded'] = encoder.transform(pred_data[col]) 
            # 或处理未知类别

    # 检查并填充缺失特征
    missing_features = [f for f in features if f not in pred_data.columns]
    for feature in missing_features:
        pred_data[feature] = 0 # 或其他填充策略
        
    # 准备输入特征向量 (确保顺序和训练时一致)
    X_pred = pred_data[features]
    
    # 标准化数值特征
    X_pred_scaled = scaler.transform(X_pred)
    
    # 使用模型进行预测
    predicted_score = model.predict(X_pred_scaled)[0]
    
    # 获取模型置信度 (或其他评估指标)
    confidence = metrics.get('confidence', 70) / 100 # 假设置信度存储在 metrics 中

except Exception as e:
    print(f"模型加载或预测失败: {e}")
    # ... 回退预测逻辑 ...

```

### 文件内容 (`simple_model.pkl`)

`.pkl` 文件通常包含一个字典或自定义对象，其中包含：

1.  **`model`**: 训练好的 LightGBM 模型实例。
2.  **`encoders`**: 一个字典，存储了用于将分类特征（如地区、职位）转换为数值的 `LabelEncoder` 对象。这对于确保预测时使用与训练时相同的编码至关重要。
3.  **`scaler`**: 一个 `StandardScaler` 对象，用于对数值特征进行标准化（使其均值为 0，标准差为 1）。预测新数据时也需要使用相同的 scaler 进行转换。
4.  **`features`**: 一个列表，包含了模型训练时使用的所有特征的名称和顺序。这确保了预测时输入给模型的特征向量具有正确的结构。
5.  **`metrics` (可选)**: 可能包含模型训练或评估时的指标，如 R² 分数、均方根误差 (RMSE) 或自定义的置信度分数。
6.  **`model_name` (可选)**: 模型的名称或描述。

### 预测流程

1.  接收用户输入的原始特征数据。
2.  加载 `simple_model.pkl` 文件。
3.  使用加载的 `encoders` 对输入的分类特征进行编码。
4.  构建特征 DataFrame，并使用加载的 `features` 列表确保特征顺序和完整性（处理缺失特征）。
5.  使用加载的 `scaler` 对特征数据进行标准化。
6.  将处理后的特征数据输入到加载的 `model` 中进行预测。
7.  获取预测结果（分数线）。
8.  （可选）从加载的 `metrics` 中获取置信度或其他评估信息。

### 注意事项

*   `.pkl` 文件依赖于创建它时使用的 Python 环境和库版本。如果环境变化过大，可能导致加载失败。
*   需要确保预测时的数据预处理步骤（编码、标准化、特征工程）与模型训练时完全一致。
*   模型需要定期重新训练以适应新的数据分布或提高准确性。 