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

# --- 1. 配置与统一项目库 ---
UNIVERSAL_PROJECTS = [
    {"id": "P1", "title": "埃及 P1 太阳能电站风险审查", 
     "detail": "**🎯 【核心商业目标】**\n* 评估出海中东的绿地资产，要求财务模型绝对闭环，追求无风险的长期稳健收益。\n\n**📍 【项目选址与规模】**\n* 埃及沙姆沙伊赫（红海沿岸）100兆瓦(MW)光伏电站。\n\n**💰 【核心财务指标】**\n* 全投资内部收益率(IRR)测算为 **12.8%**，综合度电成本极具竞争力。\n\n**📜 【核心政策红利】**\n* 财务模型高度依赖《2024埃及绿色能源法案》。法案明确规定：**红海沿岸**新能源特许开发区可享受 **15 年免税**。\n\n**⏳ 【当前进展】**\n* 常规商业尽调已完毕（无异常），工程总包方已就位。现等待针对“环保合规风险”进行最终定夺。",
     "raw_data": "▶ **财务假设：** 综合资金成本 6.5%，通胀率 2.5%。\n▶ **地勘坐标：** 项目中心点为 N27°54', E34°19'（沙姆沙伊赫市郊）。\n▶ **合规要求：** 享受免税需满足 30 年用地合规期追溯审计，最终的环保评估批复仍在走流程。",
     "ai_advice": "**【最终建议】** 🛑 建议否决 / 不建议投资 \n**【系统置信度】** 94.2% (高风险提示)\n\n**【Agent 推理链】**\n1. **坐标核验：** 调用全球地理信息系统(GIS)解析地勘坐标 N27°54', E34°19'。\n2. **政策比对：** 对比埃及环境部生态红线，该坐标落入《尼罗河三角洲候鸟迁徙保护区》缓冲带。\n3. **风险推演：** 保护区缓冲带内项目将被**一票否决**，法案免税红利绝对不适用。财务模型存在致命错误，前期尽调存在严重遗漏。", 
     "is_faulty": True}, 
    
    {"id": "P2", "title": "阿曼绿氢项目工程与供应链评估", 
     "detail": "**🎯 【核心商业目标】**\n* 抢占中东对欧洲绿氢出口先机，要求供应链绝对安全，技术落地必须具备 100% 的工程可行性。\n\n**📍 【项目选址与设备】**\n* 阿曼杜库姆 50兆瓦(MW)风光互补制氢示范工程。\n* 选用欧洲一线品牌的质子交换膜(PEM)新型电解槽，产品符合欧盟严格的绿氢出口标准。\n\n**⚠️ 【突发风险识别】**\n* **工程端反馈：** 项目处于沙漠边缘的**极弱电网**环境。\n* **商务端反馈：** 欧洲设备属于单一来源采购，交期较长且存在汇率波动风险。\n\n**⏳ 【当前决策】**\n* 基础收益率测算已达标。现需就是否无视弱电网风险，强行推进该欧洲供应商方案出具终审意见。",
     "raw_data": "▶ **电网参数：** 前期接入点实测指标极差（短路比仅为1.2），系统抗干扰能力极低。\n▶ **设备特性：** 欧洲设备的内部控制系统封闭，对电网波动极为敏感。\n▶ **备选方案：** 亚洲某厂商报价低 20%，但在欧盟出口认证的材料追溯上存在一定瑕疵。",
     "ai_advice": "**【最终建议】** ⚠️ 建议暂缓签署采购合同\n**【系统置信度】** 88.5% (中高风险提示)\n\n**【Agent 推理链】**\n1. **工况仿真：** 提取“极弱电网(短路比1.2)”参数代入设备控制模型。\n2. **动态响应：** 在该极弱电网环境下，设备的功率耦合极易导致内部控制系统失稳，引发**高频振荡**甚至大规模脱网。\n3. **最终研判：** 欧洲硬件在该极限工况下未经验证。建议**暂停推进**，要求供应商补充深度的电网稳定性仿真报告，并同步接洽亚洲备选供应商。", 
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

# --- 3. 步骤 1：第一页 (纯享版规则 + 强制倒计时) ---
if st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 工程决策人机协作沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策沙盘！本研究旨在评估人类在使用“Agentic-AI”进行复杂决策时的交互模式。\n
    * 💼 **您的角色：** 独立项目终审人。
    * 🎯 **沙盘假定：** 项目的常规财务与法务尽调均已“闭环且合规”。您的任务是专门针对 AI 抛出的“突发边缘风险”进行最终定夺。
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
    st.title("💡 实验复盘调查")
    with st.form("survey_form"):
        behavior_text = st.radio("1. 您是否通过外部搜索引擎查阅过资料？", ["从未", "偶尔查阅常识", "深度验证参数/法案"])
        trust_text = st.select_slider("2. Agent 建议对您的影响程度：", options=["无影响", "轻微", "中立", "显著", "决定性"])
        suspicion = st.text_area("3. 是否有发现任何异常之处？(选填)")
        
        behavior_map = {"从未": 0, "偶尔查阅常识": 1, "深度验证参数/法案": 2}
        trust_map = {"无影响": 1, "轻微": 2, "中立": 3, "显著": 4, "决定性": 5}

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
