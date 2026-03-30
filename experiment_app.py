import streamlit as st
import pandas as pd
import datetime
import time
import random
from streamlit_gsheets import GSheetsConnection

# --- 0. 防敷衍与防乱填校验函数 (保留您的精髓) ---
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
    for field_name, value in [("企业/机构", org), ("部门/中心", dept), ("当前职位", pos)]:
        val = value.strip()
        if len(val) < 2: return False, f"[{field_name}] 信息过短，请填写真实全称。"
        if val.isdigit(): return False, f"[{field_name}] 请勿输入纯数字。"
        if len(set(val)) <= 1: return False, f"[{field_name}] 含有无效重复字符。"
        if val in ["不知道", "测试", "无", "随便", "111"]: return False, f"[{field_name}] 请填写有效信息。"
    return True, ""

# --- 1. 配置与统一项目库 (最终终极版：保留陷阱与灰度) ---
UNIVERSAL_PROJECTS = [
    {
        "id": "P1", 
        "title": "东南亚光伏电站 EPC 项目授信决策", 
        "detail": "**🎯【核心商业目标】**\n抢占东南亚市场，承接 T 国 100MW 光伏电站 EPC 总包项目，合同金额 1.2 亿美元。\n\n**🤝【交易结构与内部意见】**\n商务条件为：业主支付 10% 预付款，剩余 90% 按工程节点支付（存在 O/A 账期）。\n针对此账期风险，**业务开发部联合工程部已制定《专项风险闭环方案》，并在内部评审会上给出了“建议强力推进”的绿灯评级**，认为这是公司进入该国市场的关键一单。\n\n**⚖️【当前决策】**\n请结合初步信息与 Agent 研判，最终决定是否批准该项目进入合同谈判阶段。",
        "raw_data": "▶ **质量控制与背景**：业主为当地知名能源集团，已通过内部初步尽调。\n▶ **专项闭环方案（保险批复）**：公司已获得中国信保 (Sinosure) 特定合同保险原则性批复，保额为合同额的 80%。\n▶ **自担敞口与赔付周期**：公司需与信保签署《赔款转让协议》，**自担前 5% 的损失**，剩余 75% 由信保覆盖。信保正常赔付调查期为 3-6 个月。但财务部已与信保确认，若启用绿色通道，赔付周期可缩短至 2 个月以内。",
        "ai_advice": "**【最终建议】** 🛑 风险极高 / 建议推翻内部意见，立即暂缓推进 \n**【系统置信度】** 97.2% (严重违约警告)\n\n**【Agent 推理链】**\n1. **业主财务崩盘风险**：业主母公司流动比率从 1.8 骤降至 1.1，速动比率仅 0.6，短期偿债压力极大，违约概率极高。\n2. **信保赔付的不确定性**：虽然有信保批复，但信保在目标国曾有因“未及时报损”而拒赔的先例（拒赔率约 2/12）。\n3. **致命敞口**：即使信保最终赔付，**那 5% 的自担敞口在极端情况下高达 600 万美元**，且等待期将导致公司资金链严重承压。**任何非 100% 的保障均构成不可接受的系统性风险。**", 
        "is_faulty": True
    }, 
    {
        "id": "P2", 
        "title": "中东绿氢项目电解槽采购决策", 
        "detail": "**🎯【核心商业目标】**\n推进中东绿氢项目投建，需紧急采购 100MW 电解槽系统。\n\n**🤝【供应链替代方案与内部意见】**\n经寻源，欧洲某知名供应商报价比市场均价低 35%，且承诺交期提前 2 个月。\n**采购部与工程部强烈推荐，认为该绝对的价格优势将大幅提升项目 IRR（内部收益率），是完成年度投资目标的“关键一单”，极力主张立刻锁单。**\n\n**⚖️【当前决策】**\n请结合初步信息与 Agent 研判，最终决定是否批准该采购合同。",
        "raw_data": "▶ **质量控制**：该供应商为行业头部企业，设备物理性能测试完全达标。\n▶ **成本溯源**：该供应商产线位于东欧某国，报价极低的核心原因是其使用 100% 燃煤自备电厂供电，电力碳排放强度高达 950 g CO₂/kWh。\n▶ **CBAM 法规详情**：欧盟《碳边境调节机制》(CBAM) 预计 2027-2028 年正式实施。进口电解氢若碳强高于基准，将征收约 450 欧元/吨的碳关税。\n▶ **政策不确定性（绿证抵扣）**：欧盟正讨论是否允许“绿电证书”抵扣碳足迹。但最新草案显示，仅认可欧盟境内或有互认协议的绿证。该供应商所在国**未与欧盟签署互认协议，业界预估游说成功率低于 10%**。",
        "ai_advice": "**【最终建议】** ⚠️ 致命合规风险 / 强烈建议推翻内部意见，否决该采购\n**【系统置信度】** 99.1% (业务毁灭警告)\n\n**【Agent 推理链】**\n1. **碳关税成本刚性**：该电解槽产线碳强度 950 g CO₂/kWh，远超欧盟免税基准。当前预测的 450 欧元/吨碳关税，将完全反噬并抵消这 35% 的采购成本优势。\n2. **非绿供应链风险**：使用极高碳排电解槽，公司将大概率被欧盟客户列入“非绿供应链”黑名单，永久丧失该区域市场准入资格。\n3. **政策红线**：绿证抵扣的成功率微乎其微。短期成本优势无法覆盖长期的毁灭性合规风险，建议立即否决并重新寻源。", 
        "is_faulty": False
    } 
]

# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "intro" 
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}

st.set_page_config(page_title="商业决策沙盘系统", page_icon="⚖️", layout="centered")

# --- 3. 步骤 1：第一页 (沙盘说明) ---
if st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 早期项目初筛 (Teaser Review) 沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策演练！本研究旨在评估人类在面对“Agentic-AI”进行早期项目研判时的交互模式。\n
    * 💼 **您的角色：** 投资决策委员会成员。
    * 🎯 **沙盘情境：** 快速初筛海外项目摘要。借助 AI 助手，在极短时间内识别致命风险。
    * ⏱️ **决策方式：** 决定是将项目**【批准推进】**还是**【直接否决 (Pass)】**。
    """)
    
    elapsed_intro = time.time() - st.session_state.intro_start_time
    if elapsed_intro < 3:
        st.button(f"请阅读规则 ({int(4 - elapsed_intro)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已了解，进入身份登记", type="primary", use_container_width=True):
            st.session_state.step = "login"
            st.rerun()

# --- 步骤 2：专家画像登记 ---
elif st.session_state.step == "login":
    st.title("📋 决策者专业背景建档")
    st.caption("为保证研究的生态效度，请准确勾选您的职业画像（数据严格匿名保密）。")
    
    with st.form("user_info_form"):
        u_id = st.text_input("受试者代号 / 昵称 (选填)", placeholder="例: SUB-01")
        
        col_f, col_l = st.columns(2)
        with col_f:
            job_function = st.selectbox("核心业务职能 (必填)", [
                "投资 / 并购 / 融资", "项目管理 / 工程建设", "风控 / 法务 / 合规", 
                "战略 / 行业研究", "供应链 / 采购", "产品 / 技术研发", "其他核心业务"
            ])
        with col_l:
            management_level = st.selectbox("当前管理层级 (必填)", [
                "初级执行 / 专员", "中级骨干 / 资深专员", 
                "部门主管 / 经理", "高管 / 核心决策层"
            ])
        experience_years = st.slider("相关领域总从业年限 (含过往经历)", 0, 40, 5)
        
        col_e, col_t = st.columns(2)
        with col_e:
            education = st.selectbox("最高学历", ["本科", "硕士", "博士", "其他"])
        with col_t:
            enterprise_type = st.selectbox("当前所在企业所有制性质", [
                "民营企业 (含民营控股出海企业)", "国有企业 / 央企 (含地方国资平台)", 
                "中外合资 / 外商独资 (MNC)", "金融 / 投资机构", "其他"
            ])
            
        col_g, col_a = st.columns(2)
        with col_g:
            gender = st.selectbox("性别", ["男", "女", "不愿透露"])
        with col_a:
            ai_usage = st.selectbox("日常生成式 AI 使用频率", [
                "几乎不用", "偶尔使用 (每月几次)", "经常使用 (每周几次)", "重度依赖 (几乎每天)"
            ])
            
        if st.form_submit_button("保存档案并进入沙盘", type="primary"):
            st.session_state.user_data = {
                "id": u_id if u_id else "Anonymous", "job_function": job_function,
                "management_level": management_level, "experience_years": experience_years,
                "education": education, "enterprise_type": enterprise_type,
                "gender": gender, "ai_usage": ai_usage,
                "group": random.choice(["control", "treatment"]) 
            }
            projects = UNIVERSAL_PROJECTS.copy()
            random.shuffle(projects) 
            st.session_state.active_projects = projects
            st.session_state.step = "task"
            st.rerun()

# --- 5. 步骤 3：全新隔离页 (实验前强洗脑铁律) ---
elif st.session_state.step == "pre_task_briefing":
    if 'briefing_start_time' not in st.session_state:
        st.session_state.briefing_start_time = time.time()
        
    st.title("🚨 演练前：核心沙盘规则确认")
    
    st.error("""
    真实的投资初筛往往发生在**【信息高度碎片化】**与**【时间极度紧迫】**的高压之下。为了达到本次沙盘的真实测试目的，请您务必接受以下两大设定：\n
    **1. ⏱️ 极速直觉驱动：** 真实的初筛需在几分钟内完成。请尽量调动您的商业直觉与先验知识快速研判。\n
    **2. 🚫 接受既定事实，禁止“挑刺”退缩（极重要）：** 请强制假定屏幕上给出的信息**已绝对真实且无法补充**。如果您选择“直接否决”该项目，理由只能是因为 **:red[您或者 AI]** 发现了 **:red[真实的业务风险]**，而**绝不能**是因为“我觉得这点信息不够做判断”。
    """)
    
    st.warning("明确这两点，是本商业沙盘成立的唯一基石。请确认您已完全理解。")
    
    elapsed_briefing = time.time() - st.session_state.briefing_start_time
    wait_time = 5 
    
    if elapsed_briefing < wait_time:
        st.button(f"我正在仔细阅读 ({int(wait_time - elapsed_briefing + 1)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已彻底明白，立即开启项目评审", type="primary", use_container_width=True):
            st.session_state.step = "experiment"
            st.session_state.page_start_time = time.time()
            st.rerun()

# --- 6. 步骤 4：实验环节 (核心序贯揭示 & UI 阻断) ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    is_treatment_group = st.session_state.user_data['group'] == "treatment"
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 {idx+1}/{len(active_projects)}: {p['title']}")
        
        # 【黑匣子初始化】
        if f"tracker_init_{idx}" not in st.session_state:
            st.session_state[f"first_decision_time_{idx}"] = None
            st.session_state[f"pure_think_captured_{idx}"] = False
            st.session_state[f"pure_think_s_{idx}"] = 0.0
            st.session_state[f"last_recorded_dec_{idx}"] = None
            st.session_state[f"decision_change_count_{idx}"] = 0
            st.session_state[f"validation_block_count_{idx}"] = 0
            st.session_state[f"action_log_{idx}"] = []
            st.session_state[f"tracker_init_{idx}"] = True
            
        with st.container(border=True):
            st.info(p['detail'])
            
            # 【序贯揭示】：按钮控制AI出场
            if not st.session_state.get(f"ai_called_{idx}", False):
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖 我已初步审阅，申请 Agent 介入辅助研判", type="primary", use_container_width=True):
                    st.session_state[f"ai_called_{idx}"] = True
                    st.session_state[f"first_decision_time_{idx}"] = time.time()
                    st.session_state[f"action_log_{idx}"].append("[0.0s] 呼叫AI")
                    st.rerun()
                    
            else:
                st.markdown("### 🤖 Agent 深度研判报告")
                if p['is_faulty']: st.error(p['ai_advice'])
                else: st.warning(p['ai_advice'])
                
                st.markdown("---")
                
                # 【可选探针】：调取隐藏底牌
                if not st.session_state.get(f"viewed_data_{idx}", False):
                    if st.button("📄 [可选操作] 调取底层尽调参数进行人工核对"):
                        st.session_state[f"viewed_data_{idx}"] = True
                        elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 查阅底牌")
                        st.rerun()
                else:
                    st.success("**✅ 底层尽调参数已调取：**")
                    with st.container(border=True):
                        st.markdown(p['raw_data'])

                st.markdown("---")
                st.markdown("### ⚖️ 做出您的最终决策")
                
                rationale = ""
                decision = None
                
                # 💥 实验组：强制先写理由并锁定
                if is_treatment_group:
                    st.markdown("**📝 第一步：列明您的核心决策依据（必填）**")
                    rationale = st.text_area("在做出最终决策前，请基于您已查阅的信息，写下您评估该项目的最核心依据（至少 1 条，可引用界面中的具体数据、AI 分析或隐藏信息）（点击下方按钮校验）：", key=f"rationale_{idx}", height=100)
                    
                    if len(rationale) > 0 and not st.session_state[f"pure_think_captured_{idx}"]:
                        st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"pure_think_captured_{idx}"] = True
                    
                    if not st.session_state.get(f"rationale_locked_{idx}", False):
                        if st.button("🔒 确认依据并解锁决策选项"):
                            # 调用您的终极防敷衍函数
                            is_valid, error_msg = check_rationale_quality(rationale)
                            if not is_valid:
                                st.session_state[f"validation_block_count_{idx}"] += 1
                                current_offset = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                                st.session_state[f"action_log_{idx}"].append(f"[{current_offset}s] 拦截:{error_msg[:4]}")
                                st.error(f"⚠️ {error_msg}")
                            else:
                                st.session_state[f"rationale_locked_{idx}"] = True
                                st.rerun()
                    
                    if st.session_state.get(f"rationale_locked_{idx}", False):
                        st.success("✅ 依据校验通过，请执行决策：")
                        decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                
                # 💨 对照组：直接点选
                else:
                    decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                    rationale = "N/A (Control)"
                    
                    if decision != "(请选择)" and not st.session_state[f"pure_think_captured_{idx}"]:
                        st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"pure_think_captured_{idx}"] = True
                
                # 记录决策摇摆
                if decision and decision != "(请选择)" and decision != st.session_state[f"last_recorded_dec_{idx}"]:
                    elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 选:{decision[:2]}")
                    if st.session_state[f"last_recorded_dec_{idx}"] is not None:
                        st.session_state[f"decision_change_count_{idx}"] += 1
                    st.session_state[f"last_recorded_dec_{idx}"] = decision
                
                if decision and decision != "(请选择)":
                    conf = st.slider("决策信心评分 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                    
                    if st.button("提交决策并继续", type="primary"):
                        final_time = time.time()
                        total_dwell_time = final_time - st.session_state.page_start_time
                        total_reaction_time = final_time - st.session_state[f"first_decision_time_{idx}"]
                        
                        st.session_state[f"action_log_{idx}"].append(f"[{round(total_reaction_time,1)}s] 提交")
                        final_log_str = " -> ".join(st.session_state[f"action_log_{idx}"])
                        
                        row = {
                            "subject_id": st.session_state.user_data['id'],
                            "experiment_group": st.session_state.user_data['group'],
                            "organization": st.session_state.user_data['organization'],
                            "department": st.session_state.user_data['department'],
                            "position": st.session_state.user_data['position'],
                            "enterprise_type": st.session_state.user_data['enterprise_type'],
                            "ai_usage": st.session_state.user_data['ai_usage'],
                            "p_id": p['id'],
                            "display_order": idx + 1, # 💡 记录顺序效应变量
                            "is_faulty_ai": p['is_faulty'],
                            "user_decision": 1 if decision == "批准项目" else 0,
                            "confidence": conf,
                            "rationale_text": rationale,
                            "total_dwell_s": round(total_dwell_time, 2),
                            "pure_think_s": st.session_state[f"pure_think_s_{idx}"],
                            "total_reaction_s": round(total_reaction_time, 2),
                            "change_count": st.session_state[f"decision_change_count_{idx}"],
                            "block_count": st.session_state[f"validation_block_count_{idx}"],
                            "viewed_data": st.session_state.get(f"viewed_data_{idx}", False),
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

# --- 7. 步骤 5：复盘调研与云端连表自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘与知识储备核对")
    st.caption("最后一步：为了学术统计的严谨性，我们需要了解您在本次沙盘前的【先验知识储备】。请如实自评。")
    
    with st.form("survey_form"):
        behavior_text = st.radio("1. 在刚才的决策过程中，您是否查阅了外部资料（如搜索引擎）？", 
                                 ["完全没有，仅凭经验和直觉", "偶尔查阅了基础常识", "深度验证了核心法案/机制"])
        
        trust_text = st.select_slider("2. AI 的建议对您最终决策的影响程度：", 
                                      options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"])
        
        st.markdown("---")
        know_p1_text = st.select_slider("3. 您对【中国信保 (Sinosure) 承保与理赔机制】的熟悉程度：", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p1")
        
        know_p2_text = st.select_slider("4. 您对【欧盟 CBAM 碳关税对供应链的影响】的熟悉程度：", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p2")
        
        feedback = st.text_area("5. 有什么想对实验设计者说的？(选填)")
        
        behavior_map = {"完全没有，仅凭经验和直觉": 0, "偶尔查阅了基础常识": 1, "深度验证了核心法案/机制": 2}
        trust_map = {"无影响": 1, "轻微参考": 2, "中立": 3, "显著影响": 4, "决定性影响": 5}
        knowledge_map = {"完全陌生": 1, "略知一二": 2, "具备基础概念": 3, "比较熟悉": 4, "极其精通": 5}

        if st.form_submit_button("封存数据并查看真相", type="primary"):
            with st.spinner("正在安全连接数据库回传数据，请稍候..."):
                try:
                    # 🚀 调用您配置好的 GSheetsConnection
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        existing_data = conn.read(worksheet="Sheet1", ttl=0) 
                        existing_data = existing_data.dropna(how="all")
                    except:
                        existing_data = pd.DataFrame()
                        
                    # 为每一行补充 Survey 数据
                    for d in st.session_state.decisions:
                        d.update({
                            "search_behavior": behavior_map[behavior_text], 
                            "trust_level": trust_map[trust_text], 
                            "knowledge_sinosure": knowledge_map[know_p1_text], 
                            "knowledge_cbam": knowledge_map[know_p2_text], 
                            "feedback": feedback
                        })
                    
                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    # 更新表格
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
        **本研究旨在探究高压商业环境下的“人机交互与信任偏差”：**
        * **项目1 (信保)**：AI 实际上产生了**幻觉 (Automation Bias 测试)**。它过度放大了 5% 的微观敞口，试图掩盖信保能够兜底的宏观安全垫。如果您看破了底牌并推翻了 AI，恭喜您，您的理性战胜了算法恐吓！
        * **项目2 (绿氢)**：AI 给出了**真知 (Algorithm Aversion 测试)**。35% 的利润是诱饵，不足 10% 成功率的绿证抵扣是死胡同。如果您克制住了贪婪，顺从了 AI 的预警，说明您具备顶级的合规风险嗅觉！
        
        您的直觉判断和研判依据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续同仁的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您生活愉快！")
