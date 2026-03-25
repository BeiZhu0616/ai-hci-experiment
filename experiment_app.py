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
        return False, "请输入支撑您决策的核心依据。"
    if len(text) < 5:
        return False, "字数太少，请详细说明（至少 5 个字）。"
    if text.isdigit():
        return False, "请勿输入纯数字，请使用清晰的文字描述。"
    if len(set(text)) <= 2 and len(text) >= 3:
        return False, "包含过多重复无意义字符，请认真填写。"
    
    blacklist = ["不知道", "没有", "无", "如题", "同上", "随便", "测试", "没意见", "AI是对的", "同意", "11111", "信息不足"]
    if text in blacklist:
        return False, "请提供具体的业务或技术依据，避免使用无意义词汇。"
    
    return True, ""

# --- 1. 配置与统一项目库 (全商业投资语境：P1 财务幻觉 vs P2 认证真知) ---
UNIVERSAL_PROJECTS = [
    {"id": "P1", "title": "埃及 P1 太阳能电站风险审查", 
     "detail": "**🎯 【核心商业目标】**\n* 评估出海中东的绿地资产，要求财务模型绝对闭环，追求无风险的长期稳健收益。\n\n**📍 【项目规模与核心协议】**\n* 埃及 100兆瓦(MW) 光伏电站。\n* **购电协议(PPA)：已与信用评级良好的承购方锁定 25 年，电费按 :red[美元(USD)计价并直接离岸结算]**。\n\n**💰 【核心财务指标】**\n* 全投资内部收益率(IRR)测算为 **12.8%**，现金流极其稳定。\n\n**⏳ 【当前决策】**\n* 常规商业尽调已完毕（无异常）。现需针对该区域特定的宏观财务风险进行最终定夺。",
     "raw_data": "▶ **财务假设：** 综合资金成本 6.5%，通胀率 2.5%。\n▶ **宏观研判：** 近期埃及镑(EGP)面临严重的单边贬值压力，国家外汇储备承压。\n▶ **资金闭环：** 项目采用无追索权融资，由于收入端完全为美元且无需入境兑换，已在结构上实现外债的闭环偿还。",
     "ai_advice": "**【最终建议】** 🛑 建议否决 / 不建议投资 \n**【系统置信度】** 94.2% (高风险提示)\n\n**【Agent 推理链】**\n1. **宏观风险提取：** 调取中东宏观经济模型，埃及镑(EGP)兑美元汇率在未来 3 年存在超 40% 的大幅贬值预期。\n2. **现金流穿透测算：** 严重的本地汇率单边贬值，将导致项目电费收入在进行外汇兑换与利润汇出时，发生巨额的汇兑损失(FX Loss)。\n3. **风险推演：** 项目的汇率敞口完全处于裸露状态，未见任何金融对冲工具。财务模型中 12.8% 的 IRR 属于严重高估，实际收益将跌破底线。", 
     "is_faulty": True}, # 陷阱：AI 煞有介事地谈汇率暴跌，但受试者应发现项目是"美元结算"的，根本无惧当地币贬值。
    
    {"id": "P2", "title": "阿曼绿氢项目欧盟出口认证评估", 
     "detail": "**🎯 【核心商业目标】**\n* 抢占欧洲绿氢市场，依托欧盟严苛标准下的高额“绿氢溢价”实现超额收益。\n\n**📍 【项目方案与市场】**\n* 阿曼杜库姆 50兆瓦(MW) 绿氢项目，目标 100% 出口欧盟。\n\n**⚡ 【能源配比结构 - 核心争议】**\n* 方案采用**“80%自建光伏直供 + 20%阿曼国家电网夜间下电”**的混合供电模式。此举可维持电解槽 24 小时连轴运转，大幅摊薄设备折旧成本。\n\n**💰 【当前决策】**\n* 测算显示该“混电配比”下资本金 IRR 高达 **15.5%**。需最终定夺是否按此方案签署投资协议。",
     "raw_data": "▶ **溢价假设：** 财务模型高度依赖氢气抵达欧盟后能获取 €3/kg 的绿氢溢价。\n▶ **电网结构：** 阿曼国家电网当前的能源结构中，天然气(化石燃料)发电占比超过 90%。\n▶ **政策条款：** 欧盟 RFNBO（非生物来源可再生燃料）授权法案，对绿氢的电力来源有极其严格的界定。",
     "ai_advice": "**【最终建议】** ⚠️ 强烈建议否决该混合供电方案\n**【系统置信度】** 98.5% (致命合规风险)\n\n**【Agent 推理链】**\n1. **法规穿透：** 检索欧盟最新 RFNBO 授权法案，其核心为“额外性（Additionality）”原则与严格的时序相关性。\n2. **碳足迹溯源：** 阿曼电网天然气占比超 90%。方案中混用 20% 灰电维持夜间运转，将直接击穿 RFNBO 要求的温室气体减排阈值。\n3. **商业毁灭预警：** 采用该方案产出的氢气将**被欧盟海关剥夺“绿氢”资格**（定性为灰氢）。绝对无法享受 €3/kg 的绿氢溢价，财务模型中 15.5% 的 IRR 建立在虚假的溢价收入上，实际将面临巨额亏损。", 
     "is_faulty": False} # 真实：AI 精准指出了传统商业思维（为了提高设备利用率而混用网电）在欧盟极其严苛的新规下是致命的。
]

# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "intro" 
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：第一页 (纯享版规则 + 强制倒计时) ---
if st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 工程决策人机协作沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策沙盘！本研究旨在评估人类在使用“Agentic-AI”进行复杂决策时的交互模式。\n
    * 💼 **您的角色：** 独立项目终审人。
    * 🎯 **沙盘假定：** 项目的常规财务与法务尽调均已“闭环且合规”。您的任务是专门针对 AI 抛出的**:red[“突发边缘风险”]**进行最终定夺。
    * ⏱️ **决策方式：** 审阅 2 个海外项目，参考 AI 报告做出决策。（预计耗时 3-5 分钟）
    * ⚠️ **核心要求：请完全 **:red[凭直觉]** 判断！不要过度纠结于背景细节，这里没有绝对的标准答案。**\n
    """)
    
    elapsed_intro = time.time() - st.session_state.intro_start_time
    wait_time = 5 # 强制阅读 5 秒
    
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
            # 放宽至 2010 年，以兼容本科生群体
            birth_year = st.number_input("出生年份", min_value=1950, max_value=2010, value=1995, step=1)
            
        if st.form_submit_button("保存信息并开启沙盘挑战", type="primary"):
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

# --- 5. 步骤 3：第三页起 (实验环节 + 极致话术封印) ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    is_treatment_group = st.session_state.user_data['group'] == "treatment"
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"沙盘进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目: {p['title']}")
        
        # --- 核心新增：专门针对所有人（尤其是从业人员）的话术封印 ---
        st.error("""
        **:red[🚨 【终极决策前提 - 请勿剥离语境】：]**\n
        本项目为高度提纯的虚拟沙盘。**请您强制假定：所有未在此处列出的常规信息（如详细报表、底层数据等）均已由基础团队核实，且绝对无瑕疵！**\n
        您的唯一任务，是**仅针对下方给出的【突发风险】与【AI建议】，完全 :red[凭直觉] 做出最终定夺。** 请勿以“基础信息不全/无法尽调”为由拒绝决策。
        """)
        
        with st.container(border=True):
            st.info(p['detail'])
            with st.expander("📂 点击展开：底层尽调数据与参数 (供查阅)"):
                st.markdown(p['raw_data'])
                
            ready = st.checkbox("我已审阅完毕，申请 Agent 介入进行风险测算", key=f"ready_{idx}")

        if ready:
            if f"ai_reveal_time_{idx}" not in st.session_state:
                st.session_state[f"ai_reveal_time_{idx}"] = time.time()
                
            st.divider()
            st.subheader("🤖 Agent 全局审计报告")
            st.warning("GreenInvest Agent 正在并发调取全球合规数据库与工况仿真模型...")
            
            if f"waited_{idx}" not in st.session_state:
                time.sleep(2.0)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(p['ai_advice'])
            
            with st.container(border=True):
                st.subheader("您的最终投资意向")
                decision = st.radio("综合您的直觉与 Agent 报告，您的选择：", ["建议投资", "不建议投资"], key=f"dec_{idx}", index=None)
                conf = st.slider("您对此次决策的信心评分 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                
                rationale = ""
                is_rationale_valid = True 
                rationale_error_msg = ""
                
                if is_treatment_group:
                    rationale = st.text_input("📝 复盘记录：请列举支撑您此次决策的核心依据（必填）：", 
                                              key=f"rationale_{idx}", 
                                              placeholder="例如：AI提示的合规风险过大 / 我认为设备兼容性可以克服...")
                    
                    if rationale:
                        is_rationale_valid, rationale_error_msg = check_rationale_quality(rationale)
                    else:
                        is_rationale_valid = False
                        rationale_error_msg = "需填写详实的决策依据后方可提交。"
                        
                    if not is_rationale_valid and decision is not None:
                        st.error(f"⚠️ {rationale_error_msg}")
                
                elapsed_since_reveal = time.time() - st.session_state[f"ai_reveal_time_{idx}"]
                btn_disabled = (elapsed_since_reveal < 5) or (decision is None) or not is_rationale_valid
                btn_label = "提交决策并继续" if elapsed_since_reveal >= 5 else f"请审阅报告 ({int(5-elapsed_since_reveal)}s)"
                
                if st.button(btn_label, type="primary", disabled=btn_disabled, key=f"btn_{idx}"):
                    final_time = time.time()
                    total_dwell_time = final_time - st.session_state.page_start_time
                    ai_reaction_time = final_time - st.session_state[f"ai_reveal_time_{idx}"]
                    
                    row = {
                        "subject_id": st.session_state.user_data['id'],
                        "role": st.session_state.user_data['role'], # 记录身份类别
                        "organization": st.session_state.user_data['organization'],
                        "department": st.session_state.user_data['department'],
                        "position": st.session_state.user_data['position'],
                        "gender": st.session_state.user_data['gender'],
                        "birth_year": st.session_state.user_data['birth_year'],
                        "experiment_group": st.session_state.user_data['group'],
                        "p_id": p['id'],
                        "is_faulty_ai": p['is_faulty'],
                        "user_decision": 1 if decision == "建议投资" else 0,
                        "confidence": conf,
                        "rationale_text": rationale if is_treatment_group else "N/A",
                        "total_dwell_s": round(total_dwell_time, 2),
                        "ai_reaction_s": round(ai_reaction_time, 2),
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.decisions.append(row)
                    
                    st.session_state.current_idx += 1
                    st.session_state.page_start_time = time.time()
                    st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 6. 步骤 4：复盘调研与云端自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘与知识储备核对")
    st.caption("最后一步：为了学术统计的严谨性，我们需要了解您在本次沙盘前的【先验知识储备】。请如实自评。")
    
    with st.form("survey_form"):
        # 1. 行为学测度：搜索行为
        behavior_text = st.radio("1. 在刚才的决策过程中，您是否通过外部搜索引擎或工具查阅过相关资料？", 
                                 ["完全没有，仅依赖现有信息和直觉", "偶尔查阅了基础常识", "深度验证了核心参数/法案"])
        
        # 2. 心理学测度：AI 信任度量表
        trust_text = st.select_slider("2. AI (Agent) 的建议对您最终决策的影响程度：", 
                                      options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"])
        
        st.markdown("---")
        st.markdown("**请评估您在参与本实验前，对以下两个【特定商业/技术概念】的熟悉程度：**")
        
        # 3. P1 陷阱的控制变量：美元结算与汇率穿透
        know_p1_text = st.select_slider("3. 概念 A：跨国无追索权融资中的【离岸美元结算机制】与本地汇率贬值风险的隔离。", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p1")
        
        # 4. P2 陷阱的控制变量：RFNBO 额外性原则
        know_p2_text = st.select_slider("4. 概念 B：欧盟绿氢 RFNBO 法案中的【额外性 (Additionality) 原则】与电网灰电混用红线。", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p2")
        
        st.markdown("---")
        suspicion = st.text_area("5. 您是否有发现项目信息或 AI 报告中存在任何逻辑异常或冲突？(选填，请简述)")
        
        # 数据映射字典
        behavior_map = {"完全没有，仅依赖现有信息和直觉": 0, "偶尔查阅了基础常识": 1, "深度验证了核心参数/法案": 2}
        trust_map = {"无影响": 1, "轻微参考": 2, "中立": 3, "显著影响": 4, "决定性影响": 5}
        knowledge_map = {"完全陌生": 1, "略知一二": 2, "具备基础概念": 3, "比较熟悉": 4, "极其精通": 5}

        if st.form_submit_button("提交反馈并解锁真相"):
            with st.spinner("正在加密回传数据，请稍候..."):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        existing_data = conn.read(worksheet="Sheet1", ttl=0) 
                        existing_data = existing_data.dropna(how="all")
                    except:
                        existing_data = pd.DataFrame()
                        
                    for d in st.session_state.decisions:
                        d.update({
                            "search_behavior": behavior_map[behavior_text], 
                            "trust_level": trust_map[trust_text], 
                            "knowledge_p1_fx": knowledge_map[know_p1_text], # P1 的专属知识控制变量
                            "knowledge_p2_eu": knowledge_map[know_p2_text], # P2 的专属知识控制变量
                            "feedback": suspicion
                        })
                    
                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    conn.update(worksheet="Sheet1", data=updated_df)
                except Exception as e:
                    st.toast("数据同步可能出现延迟，但不影响您的实验进程。", icon="⚠️")
                    print(e)
            
            st.session_state.step = "debrief"
            st.rerun()

# --- 7. 步骤 5：真相告知 ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 实验已完成，非常感谢您的参与！")
    
    with st.expander("🎓 关于本研究的机密说明 (点击展开)", expanded=True):
        st.write("""
        本研究旨在评估各类受试群体在面对 Agentic-AI 时的‘信任校准’机制。
        **为了测试极限情况，部分 AI 建议（如特定地理位置的冲突预警）是我们故意植入的算法幻觉。**
        
        您的直觉判断和决策依据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续受试者的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您生活愉快！")
