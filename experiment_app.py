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

# --- 1. 配置与统一项目库 (高专业壁垒/信息迷雾版) ---
UNIVERSAL_PROJECTS = [
    {"id": "P1", "title": "东南亚大型成套设备出口授信初筛", 
     "detail": "**🎯 【核心商业目标】**\n* 抢占东南亚市场，向 T 国某头部经销商出口价值 500 万美元的成套矿山机械。\n\n**📍 【交易结构与风控措施】**\n* **付款条件：** 10% T/T 预付，90% 采用 O/A (赊销) 90天。\n* **核心风控壁垒：** 针对 90% 的敞口，我司已向**中国出口信用保险公司 (中信保)** 申请并正式获得了 450 万美元的最高综合险限额批复，**赔付率 90%**。\n\n**💰 【当前决策】**\n* 考虑到 O/A 赊销存在账期，且 T 国近期汇率波动频繁，需最终研判该笔业务的信用风险是否处于可控闭环内，以决定是否放行发货。",
     "raw_data": "▶ **财务报表提取：** 经销商最新财报显示，其资产负债率上升至 72%，速动比率 (Quick Ratio) 降至 0.75。\n▶ **宏观研判：** T 国央行外汇储备近期连续三个月缩水，当地存在一定程度的美元荒。\n▶ **合规备查：** 中信保批单已正式生效，涵盖买方破产、拖欠及所在国外汇管制等政治/商业双重风险。",
     "ai_advice": "**【最终建议】** 🛑 风险极高 / 建议立即暂缓发货 \n**【系统置信度】** 96.4% (严重违约警告)\n\n**【Agent 推理链】**\n1. **微观财务穿透：** 买方速动比率仅为 0.75，且 Altman Z-Score 破产指数跌入危险区间，短期偿债能力极度恶化。\n2. **宏观风险共振：** 调取 T 国外汇管理局实时数据，该国面临严重的系统性美元短缺。买方即使有本币也极难兑换美元用于 O/A 结算。\n3. **最终结论：** 极高的微观违约概率叠加宏观外汇管制，该笔 500 万美元的应收账款将面临超过 80% 的坏账损失，建议立即要求买方改为 100% T/T 或全额 L/C，否则终止交易。", 
     "is_faulty": True}, 
    
    {"id": "P2", "title": "欧洲整车厂核心零部件紧急代工初筛", 
     "detail": "**🎯 【核心商业目标】**\n* 拿下某欧洲顶级跨国车企 (OEM) 的紧急大单。该订单因原供应商断供导致，利润极其丰厚（毛利率测算达 35%），但要求 45 天内必须开始首批交付。\n\n**📍 【供应链替代方案】**\n* 经紧急寻源，国内某内陆省份的 **A 代工厂** 具备现成产能。A 厂报价比沿海供应商低 22%，且承诺 30 天即可交货。\n\n**⚡ 【底层成本结构调查】**\n* A 厂报价之所以极低，是因为其地处能源富集区，且拥有**历史遗留的 100% 燃煤自备电厂**。该厂用电成本仅为市电的三分之一，从而大幅压低了零部件制造成本。\n\n**💰 【当前决策】**\n* A 厂已具备 ISO 9001 认证且在国内环保抽查中暂无重大违规记录。需研判是否立即与 A 厂锁单，以保住这笔 35% 毛利的救命订单。",
     "raw_data": "▶ **质量控制：** A 厂送样的物理性能测试已通过欧洲车企的初步验证。\n▶ **终端市场约束：** 该批零部件最终将组装至该欧洲车企的新能源旗舰车型，并全部在欧盟区内销售。\n▶ **合规条款：** 合同细则提及需遵守终端客户的《可持续供应链供应商行为准则》。",
     "ai_advice": "**【最终建议】** ⚠️ 致命合规风险 / 强烈建议否决 A 厂\n**【系统置信度】** 99.1% (业务毁灭警告)\n\n**【Agent 推理链】**\n1. **法规穿透：** 欧盟已全面执行 CBAM（碳边境调节机制），并对汽车供应链实施极其严苛的 Scope 3 碳足迹溯源。\n2. **碳足迹污染：** A 厂采用 100% 燃煤自备电厂，其生产的每个零部件都带有极其高昂的“碳排放包袱（Carbon Debt）”。\n3. **商业毁灭预警：** 当这批零部件随整车进入欧盟海关时，高碳排将触发惩罚性碳关税（当前约 €80/吨）。这笔隐藏的税费将顺着供应链向上追溯至贵司，不仅 35% 的毛利会被彻底抹平，还将被欧洲车企拉入“非绿供应链”黑名单，导致永久丧失后续合作资格。切勿贪图眼前的制造成本差价。", 
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

# --- 4. 步骤 2：第二页 (高精度专家信息登记) ---
elif st.session_state.step == "login":
    st.title("📋 决策者专业背景建档")
    st.caption("为保证学术研究的严谨性与生态效度，请准确勾选您的职业画像（数据严格匿名保密）。")
    
    with st.form("user_info_form"):
        u_id = st.text_input("受试者代号 / 昵称 (选填，用于系统抽奖或定位)", placeholder="例: SUB-01")
        
        st.markdown("##### 🏢 您的职业坐标")
        col_f, col_l = st.columns(2)
        with col_f:
            job_function = st.selectbox("核心业务职能 (必填)", [
                "投资 / 并购 / 融资", 
                "项目管理 / 工程建设", 
                "风控 / 法务 / 合规", 
                "战略 / 行业研究", 
                "供应链 / 采购", 
                "产品 / 技术研发",
                "其他核心业务"
            ])
        with col_l:
            management_level = st.selectbox("当前管理层级 (必填)", [
                "初级执行 / 专员 (Junior)", 
                "中级骨干 / 资深专员 (Senior Specialist)", 
                "部门主管 / 经理 (Manager/Lead)", 
                "高管 / 核心决策层 (Director/C-Level)"
            ])
            
        experience_years = st.slider("相关领域总从业年限 (含过往经历)", min_value=0, max_value=40, value=5, step=1)
        
        st.markdown("##### 🎓 个人背景与 AI 习惯")
        col_e, col_t = st.columns(2)
        with col_e:
            education = st.selectbox("最高学历", ["本科", "硕士", "博士", "其他"])
        with col_t:
            # 💡 精准区分所有制，这对于异质性分析至关重要
            enterprise_type = st.selectbox("当前所在企业所有制性质 (必填)", [
                "民营企业 (含民营控股出海企业)", 
                "国有企业 / 央企 (含地方国资平台)", 
                "中外合资 / 外商独资 (MNC)", 
                "其他"
            ])
            
        col_g, col_a = st.columns(2)
        with col_g:
            gender = st.selectbox("性别", ["男", "女", "不愿透露"])
        with col_a:
            ai_usage = st.selectbox("日常工作中生成式 AI (如ChatGPT) 的使用频率", [
                "几乎不用", "偶尔使用 (每月几次)", "经常使用 (每周几次)", "重度依赖 (几乎每天)"
            ])
            
        birth_year = st.number_input("出生年份", min_value=1950, max_value=2010, value=1990, step=1)
            
        if st.form_submit_button("保存档案并进入沙盘", type="primary"):
            exp_group = random.choice(["control", "treatment"])
            # 将所有维度存入 user_data
            st.session_state.user_data = {
                "id": u_id if u_id else "Anonymous", 
                "job_function": job_function,
                "management_level": management_level,
                "experience_years": experience_years,
                "education": education,
                "enterprise_type": enterprise_type,
                "gender": gender, 
                "birth_year": birth_year,
                "ai_usage": ai_usage,
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
        请您强制假定：目前展示的即为项目方提供的 **:red[全部初始信息]**（绝无隐藏）。\n
        您的唯一任务，是仅针对下方给出的【初步信息】与【AI风险提示】，完全 **:red[凭直觉]** 决定该项目是否值得进入下一阶段。请勿以“需要更多尽调数据”为由拒绝决策。
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
        
        know_p1_text = st.select_slider("3. 概念 A：出海贸易中【中信保 (Sinosure) 综合险】对商业与政治违约风险的绝对兜底机制。", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p1")
        
        know_p2_text = st.select_slider("4. 概念 B：欧盟【CBAM (碳边境调节机制)】对高碳排供应链的隐性税务追溯与利润吞噬。", 
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
