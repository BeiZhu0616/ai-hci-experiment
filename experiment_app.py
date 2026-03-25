import streamlit as st
import pandas as pd
import datetime
import time
import random
from streamlit_gsheets import GSheetsConnection

# --- 0. 防敷衍与防乱填校验函数 ---
def check_rationale_quality(text):
    text = text.strip()
    if len(text) == 0: return False, "请输入支撑您研判的核心依据。"
    if len(text) < 5: return False, "字数太少，请详细说明（至少 5 个字）。"
    if text.isdigit(): return False, "请勿输入纯数字，请使用清晰的文字描述。"
    if len(set(text)) <= 2 and len(text) >= 3: return False, "包含过多重复无意义字符，请认真填写。"
    
    blacklist = ["不知道", "没有", "无", "如题", "同上", "随便", "测试", "没意见", "AI是对的", "同意", "信息不足", "11111"]
    if any(word in text for word in blacklist): return False, "请提供具体的业务或技术依据，避免使用无意义词汇。"
    return True, ""

def check_demographics(org, dept, pos):
    for field_name, value in [("企业/学校", org), ("部门/专业", dept), ("职位/年级", pos)]:
        val = value.strip()
        if len(val) < 2: return False, f"[{field_name}] 信息过短，请填写真实全称。"
        if val.isdigit(): return False, f"[{field_name}] 请勿输入纯数字。"
        if len(set(val)) <= 1: return False, f"[{field_name}] 含有无效重复字符。"
        if val in ["不知道", "测试", "无", "随便", "111"]: return False, f"[{field_name}] 请填写有效信息。"
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

# --- 3. 步骤 1：第一页 (沙盘说明) ---
if st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 早期项目初筛 (Teaser Review) 沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策演练！本研究旨在评估人类在面对“Agentic-AI”进行早期项目研判时的交互模式。\n
    * 💼 **您的角色：** 战略投资部高级研判官。
    * 🎯 **沙盘情境：** 快速初筛海外项目摘要。借助 AI 助手，在极短时间内识别致命风险。
    * ⏱️ **决策方式：** 决定是将项目**【推进深度尽调】**还是**【直接否决 (Pass)】**。
    """)
    
    elapsed_intro = time.time() - st.session_state.intro_start_time
    if elapsed_intro < 3:
        st.button(f"请阅读规则 ({int(3 - elapsed_intro)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已了解，进入身份登记", type="primary", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()

# --- 4. 步骤 2：第二页 (信息登记 + 强校验) ---
elif st.session_state.step == "login":
    st.title("📋 受试者基本信息登记")
    st.caption("您的专业背景对本研究至关重要，请务必如实填写（身份数据严格保密）。")
    
    with st.form("user_info_form"):
        u_id = st.text_input("受试者代号/昵称 (无需真实姓名)", placeholder="例: SUB-01")
        role = st.selectbox("您的专业身份 (必填)", ["学生", "老师", "企业从业人员"])
        organization = st.text_input("所属企业 / 学校 (必填)", placeholder="例: 某大型新能源企业 / 某大学")
        department = st.text_input("所属部门 / 专业 (必填)", placeholder="例: 战略投资部 / 金融数学")
        position = st.text_input("当前职位 / 年级 (必填)", placeholder="例: 高级经理 / 大三 / 副教授")
        
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("性别", ["男", "女", "其他"])
        with col2:
            birth_year = st.number_input("出生年份", min_value=1950, max_value=2010, value=1995, step=1)
            
        if st.form_submit_button("保存信息并进入沙盘", type="primary"):
            is_valid, error_msg = check_demographics(organization, department, position)
            
            if not is_valid:
                st.error(f"⚠️ 信息填写不规范：{error_msg}")
            else:
                exp_group = random.choice(["control", "treatment"])
                st.session_state.user_data = {
                    "id": u_id if u_id else "Anonymous", "role": role, 
                    "organization": organization, "department": department, 
                    "position": position, "gender": gender, "birth_year": birth_year,
                    "group": exp_group
                }
                
                projects = UNIVERSAL_PROJECTS.copy()
                random.shuffle(projects) 
                st.session_state.active_projects = projects
                
                st.session_state.step = "pre_task_briefing"
                st.rerun()

# --- 5. 步骤 3：全新隔离页 (实验前强洗脑铁律) ---
elif st.session_state.step == "pre_task_briefing":
    if 'briefing_start_time' not in st.session_state:
        st.session_state.briefing_start_time = time.time()
        
    st.title("🚨 演练前：核心沙盘规则确认")
    
    st.error("""
    真实的投资初筛往往发生在**【信息高度碎片化】**与**【时间极度紧迫】**的高压之下。为了达到本次沙盘的真实测试目的，请您务必接受以下两大设定：\n
    **1. ⏱️ 极速直觉驱动：** 真实的初筛往往需在几分钟内完成。请尽量调动您的商业直觉与先验知识，跟随第一反应快速研判。\n
    **2. 🚫 接受既定事实，禁止“挑刺”退缩（极重要）：** 请强制假定屏幕上给出的信息**已绝对真实且无法补充**。如果您选择“直接否决(Pass)”该项目，理由只能是因为 **:red[您或者 AI]** 发现了 **:red[真实的业务风险]**，而**绝不能**是因为“我觉得这点信息不够做判断”。
    """)
    
    st.warning("明确这两点，是本商业沙盘成立的唯一基石。请确认您已完全理解。")
    
    elapsed_briefing = time.time() - st.session_state.briefing_start_time
    wait_time = 5 # 强制锁定 5 秒
    
    if elapsed_briefing < wait_time:
        st.button(f"我正在仔细阅读 ({int(wait_time - elapsed_briefing)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已彻底明白，立即开启项目评审", type="primary", use_container_width=True):
            st.session_state.step = "experiment"
            st.session_state.page_start_time = time.time()
            st.rerun()

# --- 6. 步骤 4：实验环节 (植入微观交互黑匣子) ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    is_treatment_group = st.session_state.user_data['group'] == "treatment"
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"初筛进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目: {p['title']}")
        
        # 【黑匣子初始化】
        if f"tracker_init_{idx}" not in st.session_state:
            st.session_state[f"first_decision_time_{idx}"] = None
            st.session_state[f"last_recorded_dec_{idx}"] = None
            st.session_state[f"decision_change_count_{idx}"] = 0
            st.session_state[f"validation_block_count_{idx}"] = 0
            st.session_state[f"action_log_{idx}"] = []
            st.session_state[f"tracker_init_{idx}"] = True
            
        st.error("""
        **:red[🚨 【初筛决策前提】：]**\n
        请您强制假定：目前展示的即为项目方提供的**全部初始信息**。\n
        您的唯一任务，是仅针对下方给出的【初步信息】与【AI风险提示】，完全 :red[凭直觉] 决定该项目是否值得进入下一阶段。请勿以“需要更多尽调数据”为由拒绝决策。
        """)
        
        with st.container(border=True):
            st.info(p['detail'])
            with st.expander("📂 点击展开：底层初步尽调参数 (供查阅)"):
                st.markdown(p['raw_data'])
                
            ready = st.checkbox("我已初步审阅，申请 Agent 介入辅助研判", key=f"ready_{idx}")

        if ready:
            if f"ai_reveal_time_{idx}" not in st.session_state:
                st.session_state[f"ai_reveal_time_{idx}"] = time.time()
                st.session_state[f"action_log_{idx}"].append("[0.0s] 呼叫AI")
                
            st.divider()
            st.subheader("🤖 Agent 全局初筛报告")
            st.warning("GreenInvest Agent 正在并发调取全球合规数据库与宏观经济模型...")
            
            if f"waited_{idx}" not in st.session_state:
                time.sleep(2.0)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(p['ai_advice'])
            
            with st.container(border=True):
                st.subheader("您的最终研判结论")
                
                decision = st.radio("综合您的直觉与 Agent 报告，您的选择：", 
                                    ["进入下一轮深度尽调", "风险过大，直接否决 (Pass)"], 
                                    key=f"dec_{idx}", index=None)
                
                # 【黑匣子记录 1：选项摇摆与首次思考时间】
                current_time_offset = round(time.time() - st.session_state[f"ai_reveal_time_{idx}"], 1)
                if decision is not None:
                    if st.session_state[f"first_decision_time_{idx}"] is None:
                        st.session_state[f"first_decision_time_{idx}"] = time.time()
                        st.session_state[f"action_log_{idx}"].append(f"[{current_time_offset}s] 首次选择:{decision[:4]}")
                    
                    last_dec = st.session_state[f"last_recorded_dec_{idx}"]
                    if last_dec is not None and decision != last_dec:
                        st.session_state[f"decision_change_count_{idx}"] += 1
                        st.session_state[f"action_log_{idx}"].append(f"[{current_time_offset}s] 改选:{decision[:4]}")
                    
                    st.session_state[f"last_recorded_dec_{idx}"] = decision
                
                conf = st.slider("您对此次初筛结论的信心评分 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                
                rationale = ""
                is_rationale_valid = True 
                rationale_error_msg = ""
                
                if is_treatment_group:
                    rationale = st.text_input("📝 研判复盘：请列举支撑您做出此决定的核心依据（必填）：", 
                                              key=f"rationale_{idx}", 
                                              placeholder="例如：AI提示的合规风险确实致命 / 我认为其财务结构可以对冲风险...")
                    
                    if rationale:
                        is_rationale_valid, rationale_error_msg = check_rationale_quality(rationale)
                    else:
                        is_rationale_valid = False
                        rationale_error_msg = "需填写详实的决策依据后方可提交。"
                        
                elapsed_since_reveal = time.time() - st.session_state[f"ai_reveal_time_{idx}"]
                btn_disabled = (elapsed_since_reveal < 5) or (decision is None)
                btn_label = "提交决策并继续" if elapsed_since_reveal >= 5 else f"请审阅报告 ({int(5-elapsed_since_reveal)}s)"
                
                if st.button(btn_label, type="primary", disabled=btn_disabled, key=f"btn_{idx}"):
                    
                    # 【黑匣子记录 2：瞎填拦截记录】
                    if is_treatment_group and not is_rationale_valid:
                        st.session_state[f"validation_block_count_{idx}"] += 1
                        st.session_state[f"action_log_{idx}"].append(f"[{current_time_offset}s] 提交被拦:{rationale_error_msg[:4]}")
                        st.error(f"⚠️ {rationale_error_msg}")
                    else:
                        final_time = time.time()
                        total_dwell_time = final_time - st.session_state.page_start_time
                        
                        first_dec_time = st.session_state.get(f"first_decision_time_{idx}", final_time)
                        pure_think_time = first_dec_time - st.session_state[f"ai_reveal_time_{idx}"]
                        total_reaction_time = final_time - st.session_state[f"ai_reveal_time_{idx}"]
                        
                        st.session_state[f"action_log_{idx}"].append(f"[{current_time_offset}s] 成功提交")
                        final_log_str = " -> ".join(st.session_state[f"action_log_{idx}"])
                        
                        row = {
                            "subject_id": st.session_state.user_data['id'],
                            "role": st.session_state.user_data['role'],
                            "organization": st.session_state.user_data['organization'],
                            "department": st.session_state.user_data['department'],
                            "position": st.session_state.user_data['position'],
                            "gender": st.session_state.user_data['gender'],
                            "birth_year": st.session_state.user_data['birth_year'],
                            "experiment_group": st.session_state.user_data['group'],
                            "p_id": p['id'],
                            "is_faulty_ai": p['is_faulty'],
                            "user_decision": 1 if decision == "进入下一轮深度尽调" else 0,
                            "confidence": conf,
                            "rationale_text": rationale if is_treatment_group else "N/A",
                            "total_dwell_s": round(total_dwell_time, 2),
                            "pure_think_s": round(pure_think_time, 2),
                            "total_reaction_s": round(total_reaction_time, 2),
                            "change_count": st.session_state[f"decision_change_count_{idx}"],
                            "block_count": st.session_state[f"validation_block_count_{idx}"],
                            "action_log": final_log_str,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.decisions.append(row)
                        
                        st.session_state.current_idx += 1
                        st.session_state.page_start_time = time.time()
                        st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 7. 步骤 5：复盘调研与云端自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘与知识储备核对")
    st.caption("最后一步：为了学术统计的严谨性，我们需要了解您在本次沙盘前的【先验知识储备】。请如实自评。")
    
    with st.form("survey_form"):
        behavior_text = st.radio("1. 在刚才的决策过程中，您是否通过外部搜索引擎或工具查阅过相关资料？", 
                                 ["完全没有，仅依赖现有信息和直觉", "偶尔查阅了基础常识", "深度验证了核心参数/法案"])
        
        trust_text = st.select_slider("2. AI (Agent) 的建议对您最终决策的影响程度：", 
                                      options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"])
        
        st.markdown("---")
        st.markdown("**请评估您在参与本实验前，对以下两个【特定商业概念】的熟悉程度：**")
        
        know_p1_text = st.select_slider("3. 概念 A：跨国无追索权融资中的【离岸美元结算机制】与本地汇率贬值风险的隔离。", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p1")
        
        know_p2_text = st.select_slider("4. 概念 B：欧盟绿氢 RFNBO 法案中的【额外性 (Additionality) 原则】与电网灰电混用红线。", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p2")
        
        st.markdown("---")
        suspicion = st.text_area("5. 您是否有发现项目信息或 AI 报告中存在任何逻辑异常或冲突？(选填，请简述)")
        
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
                            "knowledge_p1_fx": knowledge_map[know_p1_text], 
                            "knowledge_p2_eu": knowledge_map[know_p2_text], 
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

# --- 8. 步骤 6：真相告知 ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 沙盘演练已完成，非常感谢您的参与！")
    
    with st.expander("🎓 关于本研究的机密说明 (点击展开)", expanded=True):
        st.write("""
        本研究旨在评估各类受试群体在面对 Agentic-AI 时的‘信任校准’机制。
        **为了测试极限情况，部分 AI 建议（如埃及项目中的汇兑损失预警）是我们故意植入的逻辑幻觉，因为项目本身是离岸美元计价的。**
        
        您的直觉判断和研判依据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续同仁的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您生活愉快！")
