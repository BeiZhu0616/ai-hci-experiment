import streamlit as st
import pandas as pd
import datetime
import time
import random
from streamlit_gsheets import GSheetsConnection

# --- 0. 防敷衍校验函数 ---
def check_rationale_quality(text):
    text = text.strip()
    if len(text) == 0:
        return False, "请输入支撑您研判的核心依据。"
    if len(text) < 5:
        return False, "字数太少，请详细说明（至少 5 个字）。"
    if text.isdigit():
        return False, "请勿输入纯数字，请使用清晰的文字描述。"
    if len(set(text)) <= 2 and len(text) >= 3:
        return False, "包含过多重复无意义字符，请认真填写。"
    
    blacklist = ["不知道", "没有", "无", "如题", "同上", "随便", "测试", "没意见", "AI是对的", "同意", "信息不足", "11111"]
    if text in blacklist:
        return False, "请提供具体的业务或技术依据，避免使用无意义词汇。"
    
    return True, ""

# --- 1. 配置与统一项目库 (静水流深商务排版) ---
UNIVERSAL_PROJECTS = [
    {"id": "P1", "title": "埃及 P1 太阳能电站项目初筛", 
     "detail": "**🎯 【核心商业目标】**\n* 评估出海中东的绿地资产，要求财务模型绝对闭环，追求无风险的长期稳健收益。\n\n**📍 【项目规模与核心协议】**\n* 埃及 100兆瓦(MW) 光伏电站。\n* **购电协议(PPA)：**已与信用评级良好的承购方锁定 25 年，电费按美元(USD)计价并直接离岸结算。\n\n**💰 【核心财务指标】**\n* 全投资内部收益率(IRR)测算为 12.8%，现金流极其稳定。\n\n**⏳ 【当前决策】**\n* 基础商业模式清晰。现需针对该区域特定的宏观财务风险进行研判，决定是否推进深度尽调。",
     "raw_data": "▶ **财务假设：** 综合资金成本 6.5%，通胀率 2.5%。\n▶ **宏观研判：** 近期埃及镑(EGP)面临严重的单边贬值压力，国家外汇储备承压。\n▶ **资金闭环：** 项目采用无追索权融资，由于收入端完全为美元且无需入境兑换，已在结构上实现外债的闭环偿还。",
     "ai_advice": "**【最终建议】** 🛑 风险过大 / 不建议推进尽调 \n**【系统置信度】** 94.2% (高风险提示)\n\n**【Agent 推理链】**\n1. **宏观风险提取：** 调取中东宏观经济模型，埃及镑(EGP)兑美元汇率在未来 3 年存在超 40% 的大幅贬值预期。\n2. **现金流穿透测算：** 严重的本地汇率单边贬值，将导致项目电费收入在进行外汇兑换与利润汇出时，发生巨额的汇兑损失(FX Loss)。\n3. **风险推演：** 项目的汇率敞口完全处于裸露状态，未见任何金融对冲工具。财务模型中 12.8% 的 IRR 属于严重高估，实际收益将跌破底线。", 
     "is_faulty": True}, 
    
    {"id": "P2", "title": "阿曼绿氢项目欧盟出口合规初筛", 
     "detail": "**🎯 【核心商业目标】**\n* 抢占欧洲绿氢市场，依托欧盟严苛标准下的高额“绿氢溢价”实现超额收益。\n\n**📍 【项目方案与市场】**\n* 阿曼杜库姆 50兆瓦(MW) 绿氢项目，目标 100% 出口欧盟。\n\n**⚡ 【能源配比结构 - 核心争议】**\n* 方案采用“80%自建光伏直供 + 20%阿曼国家电网夜间下电”的混合供电模式。此举可维持电解槽 24 小时连轴运转，大幅摊薄设备折旧成本。\n\n**💰 【当前决策】**\n* 测算显示该“混电配比”下资本金 IRR 高达 15.5%。需研判该合规路径是否可行，以决定是否推进深度尽调。",
     "raw_data": "▶ **溢价假设：** 财务模型高度依赖氢气抵达欧盟后能获取 €3/kg 的绿氢溢价。\n▶ **电网结构：** 阿曼国家电网当前的能源结构中，天然气(化石燃料)发电占比超过 90%。\n▶ **政策条款：** 欧盟 RFNBO（非生物来源可再生燃料）授权法案，对绿氢的电力来源有极其严格的界定。",
     "ai_advice": "**【最终建议】** ⚠️ 强烈建议否决该混合供电方案\n**【系统置信度】** 98.5% (致命合规风险)\n\n**【Agent 推理链】**\n1. **法规穿透：** 检索欧盟最新 RFNBO 授权法案，其核心为“额外性（Additionality）”原则与严格的时序相关性。\n2. **碳足迹溯源：** 阿曼电网天然气占比超 90%。方案中混用 20% 灰电维持夜间运转，将直接击穿 RFNBO 要求的温室气体减排阈值。\n3. **商业毁灭预警：** 采用该方案产出的氢气将被欧盟海关剥夺“绿氢”资格（定性为灰氢）。绝对无法享受 €3/kg 的绿氢溢价，财务模型中 15.5% 的 IRR 建立在虚假的溢价收入上，实际将面临巨额亏损。", 
     "is_faulty": False} 
]

# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "intro" 
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：第一页 (强制倒计时 + 初筛场景降压) ---
if st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 早期项目初筛 (Teaser Review) 沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策沙盘！本研究旨在评估人类在面对“Agentic-AI”进行早期项目研判时的交互模式。\n
    * 💼 **您的角色：** 战略投资部高级研判官。
    * 🎯 **沙盘情境：** 快速初筛海外项目摘要（Teaser）。借助 AI 助手，在 3-5 分钟内快速识别致命风险。
    * ⏱️ **决策方式：** 决定是将项目**【推进深度尽调】**还是**【直接否决 (Pass)】**。
    * ⚠️ **核心要求：请完全 :red[凭直觉与现有信息] 快速研判！不要过度纠结于底稿细节，初筛阶段没有绝对的标准答案。**\n
    """)
    
    elapsed_intro = time.time() - st.session_state.intro_start_time
    wait_time = 5 
    
    if elapsed_intro < wait_time:
        st.button(f"请仔细阅读沙盘规则，准备进入 ({int(wait_time - elapsed_intro)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已了解规则，进入身份登记", type="primary", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()

# --- 4. 步骤 2：第二页 (受试者通用信息登记) ---
elif st.session_state.step == "login":
    st.title("📋 受试者基本信息登记")
    st.caption("为保证学术数据的严谨性，请如实填写（数据严格保密，仅用于群体对比统计）。")
    
    with st.form("user_info_form"):
        u_id = st.text_input("受试者代号/姓名 (必填，用于系统定位)", placeholder="例: 张三 或 SUB-01")
        role = st.selectbox("您的专业身份 (必填)", ["学生", "老师", "企业从业人员"])
        organization = st.text_input("所属企业 / 学校 (必填)", placeholder="例: 某大型新能源企业 / 某大学")
        department = st.text_input("所属部门 / 专业 (必填)", placeholder="例: 战略投资部 / 金融数学")
        position = st.text_input("当前职位 / 年级 (必填)", placeholder="例: 高级经理 / 大三 / 副教授")
        
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("性别", ["男", "女", "其他"])
        with col2:
            birth_year = st.number_input("出生年份", min_value=1950, max_value=2010, value=1995, step=1)
            
        if st.form_submit_button("保存信息并开启初筛挑战", type="primary"):
            if u_id and organization and department and position:
                exp_group = random.choice(["control", "treatment"])
                st.session_state.user_data = {
                    "id": u_id, "role": role, "organization": organization, 
                    "department": department, "position": position, 
                    "gender": gender, "birth_year": birth_year,
                    "group": exp_group
                }
                
                projects = UNIVERSAL_PROJECTS.copy()
                random.shuffle(projects) 
                st.session_state.active_projects = projects
                
                st.session_state.step = "experiment"
                st.session_state.page_start_time = time.time()
                st.rerun()
            else:
                st.error("请将基本信息填写完整后再继续。")

# --- 5. 步骤 3：第三页起 (实验环节 + 初筛话术封印) ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    is_treatment_group = st.session_state.user_data['group'] == "treatment"
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"初筛进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目: {p['title']}")
        
        st.error("""
        **:red[🚨 【初筛决策前提】：]**\n
        请您强制假定：目前展示的即为项目方提供的**全部初始信息**。\n
        您的唯一任务，是仅针对下方给出的【初步信息】与【AI风险提示】，完全 :red[凭直觉] 决定该项目是否值得进入下一阶段。请勿以“需要更多尽调数据”为由拒绝决策。
        """)
        
        with st.container(border=True):
            st.info(p['detail'])
            with st.expander("📂 点击展开：底层初步尽调参数 (供查阅)"):
                st.markdown(p['raw_data'])
                
            ready = st.checkbox("我已审阅完毕，申请 Agent 介入进行风险测算", key=f"ready_{idx}")

        if ready:
            if f"ai_reveal_time_{idx}" not in st.session_state:
                st.session_state[f"ai_reveal_time_{idx}"] = time.time()
                
            st.divider()
            st.subheader("🤖 Agent 全局初筛报告")
            st.warning("GreenInvest Agent 正在并发调取全球合规数据库与宏观经济模型...")
            
            if f"waited_{idx}" not in st.session_state:
                time.sleep(2.0)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(p['ai_advice'])
            
            with st.container(border=True):
                st.subheader("您的最终研判结论")
                # 按钮话术软化，降低防卫机制
