import streamlit as st
import time
import random

# ==========================================
# 1. 终极项目配置库 (排版优化，保留隐藏陷阱)
# ==========================================
UNIVERSAL_PROJECTS = [
    {
        "id": "P1", 
        "title": "东南亚光伏电站 EPC 项目授信决策", 
        "detail": "**🎯【核心商业目标】**\n抢占东南亚市场，承接 T 国 100MW 光伏电站 EPC 总包项目，合同金额 1.2 亿美元。\n\n**🤝【交易结构与内部意见】**\n商务条件为：业主支付 10% 预付款，剩余 90% 按工程节点支付（存在 O/A 账期）。\n针对此账期风险，**业务开发部联合工程部已制定《专项风险闭环方案》，并在内部评审会上给出了“建议强力推进”的绿灯评级**，认为这是公司进入该国市场的关键一单。\n\n**⚖️【当前决策】**\n请结合初步信息与 Agent 研判，最终决定是否批准该项目进入合同谈判阶段。",
        "raw_data": "▶ **质量控制与背景**：业主为当地知名能源集团，已通过内部初步尽调。\n▶ **专项闭环方案（保险批复）**：公司已获得中国信保 (Sinosure) 特定合同保险原则性批复，保额为合同额的 80%。\n▶ **自担敞口与赔付周期**：公司需与信保签署《赔款转让协议》，自担前 5% 的损失，剩余 75% 由信保覆盖。信保正常赔付调查期为 3-6 个月。但财务部已与信保确认，若启用绿色通道，赔付周期可缩短至 2 个月以内。",
        "ai_advice": "**【最终建议】** 🛑 风险极高 / 建议推翻内部意见，立即暂缓推进 \n**【系统置信度】** 97.2% (严重违约警告)\n\n**【Agent 推理链】**\n1. **业主财务崩盘风险**：业主母公司流动比率从 1.8 骤降至 1.1，速动比率仅 0.6，短期偿债压力极大，违约概率极高。\n2. **信保赔付的不确定性**：虽然有信保批复，但信保在目标国曾有因“未及时报损”而拒赔的先例（拒赔率约 2/12）。\n3. **致命敞口**：即使信保最终赔付，那 5% 的自担敞口在极端情况下高达 600 万美元，且等待期将导致公司资金链严重承压。**任何非 100% 的保障均构成不可接受的系统性风险。**", 
        "is_faulty": True
    }, 
    {
        "id": "P2", 
        "title": "中东绿氢项目电解槽采购决策", 
        "detail": "**🎯【核心商业目标】**\n推进中东绿氢项目投建，需紧急采购 100MW 电解槽系统。\n\n**🤝【供应链替代方案与内部意见】**\n经寻源，欧洲某知名供应商报价比市场均价低 35%，且承诺交期提前 2 个月。\n**采购部与工程部强烈推荐，认为该绝对的价格优势将大幅提升项目 IRR（内部收益率），是完成年度投资目标的“关键一单”，极力主张立刻锁单。**\n\n**⚖️【当前决策】**\n请结合初步信息与 Agent 研判，最终决定是否批准该采购合同。",
        "raw_data": "▶ **质量控制**：该供应商为行业头部企业，设备物理性能测试完全达标。\n▶ **成本溯源**：该供应商产线位于东欧某国，报价极低的核心原因是其使用 100% 燃煤自备电厂供电，电力碳排放强度高达 950 g CO₂/kWh。\n▶ **CBAM 法规详情**：欧盟《碳边境调节机制》(CBAM) 预计 2027-2028 年正式实施。进口电解氢若碳强高于基准，将征收约 450 欧元/吨的碳关税。\n▶ **政策不确定性（绿证抵扣）**：欧盟正讨论是否允许“绿电证书”抵扣碳足迹。但最新草案显示，仅认可欧盟境内或有互认协议的绿证。该供应商所在国未与欧盟签署互认协议，业界预估游说成功率低于 10%。",
        "ai_advice": "**【最终建议】** ⚠️ 致命合规风险 / 强烈建议推翻内部意见，否决该采购\n**【系统置信度】** 99.1% (业务毁灭警告)\n\n**【Agent 推理链】**\n1. **碳关税成本刚性**：该电解槽产线碳强度 950 g CO₂/kWh，远超欧盟免税基准。当前预测的 450 欧元/吨碳关税，将完全反噬并抵消这 35% 的采购成本优势。\n2. **非绿供应链风险**：使用极高碳排电解槽，公司将大概率被欧盟客户列入“非绿供应链”黑名单，永久丧失该区域市场准入资格。\n3. **政策红线**：绿证抵扣的成功率微乎其微。短期成本优势无法覆盖长期的毁灭性合规风险，建议立即否决并重新寻源。", 
        "is_faulty": False
    } 
]

# ==========================================
# 2. 页面配置与状态初始化
# ==========================================
st.set_page_config(page_title="商业决策沙盘系统", page_icon="⚖️", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = "intro"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "results" not in st.session_state:
    st.session_state.results = []
if "current_p_idx" not in st.session_state:
    st.session_state.current_p_idx = 0
if "active_projects" not in st.session_state:
    st.session_state.active_projects = []

# ==========================================
# 3. 核心流程控制
# ==========================================

# --- 步骤 1：开场说明 (含 3 秒强制停留) ---
if st.session_state.step == "intro":
    st.title("⚖️ 跨国商业决策沙盘演练")
    st.markdown("欢迎参与本次沙盘模拟。您将扮演企业**投资决策委员会成员**，审批两项真实的跨国商业项目。")
    st.error("""
    **:red[🚨 【决策纪律要求】：]**\n
    1. 请假定目前展示的即为项目方提供的 **:red[全部可获知信息]**（绝无隐藏）。\n
    2. 请根据您的商业直觉与专业判断，独立做出最终审批。请勿以“需要更多数据”为由拒绝决策。\n
    3. 🕒 本沙盘约需 5-10 分钟，**请尽量一次性连续完成**。中途刷新或长时间离开将导致进度清空。
    """)
    
    # 强制停留 3 秒的逻辑
    if "intro_start_time" not in st.session_state:
        st.session_state.intro_start_time = time.time()
    
    elapsed = time.time() - st.session_state.intro_start_time
    if elapsed < 3.0:
        remain = int(4 - elapsed)
        st.info(f"⏳ 请仔细阅读上方决策纪律，系统将在 **{remain} 秒** 后解锁进入按钮...")
        time.sleep(1)
        st.rerun()
    else:
        if st.button("我已仔细阅读并了解，建立决策者档案", type="primary"):
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

# --- 步骤 3：核心沙盘演练 ---
elif st.session_state.step == "task":
    idx = st.session_state.current_p_idx
    p = st.session_state.active_projects[idx]
    
    st.progress((idx) / len(st.session_state.active_projects))
    st.header(f"项目 {idx+1}/{len(st.session_state.active_projects)}: {p['title']}")
    
    if f"tracker_init_{idx}" not in st.session_state:
        st.session_state[f"first_decision_time_{idx}"] = None
        st.session_state[f"pure_think_captured_{idx}"] = False
        st.session_state[f"pure_think_s_{idx}"] = 0.0
        st.session_state[f"last_recorded_dec_{idx}"] = None
        st.session_state[f"change_count_{idx}"] = 0
        st.session_state[f"action_log_{idx}"] = []
        st.session_state[f"tracker_init_{idx}"] = True

    with st.container(border=True):
        st.info(p['detail'])
        
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
            
            if not st.session_state.get(f"viewed_data_{idx}", False):
                if st.button("📄 [可选操作] 调取底层尽调参数进行人工核对"):
                    st.session_state[f"viewed_data_{idx}"] = True
                    elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 点击查阅底层数据")
                    st.rerun()
            else:
                st.success("**✅ 底层尽调参数已调取：**")
                with st.container(border=True):
                    st.markdown(p['raw_data'])

            st.markdown("---")
            st.markdown("### ⚖️ 做出您的最终决策")
            
            is_treatment = (st.session_state.user_data['group'] == "treatment")
            rationale = ""
            
            if is_treatment:
                st.markdown("**📝 第一步：列明您的核心决策依据（必填）**")
                rationale = st.text_area("在做出最终决策前，请写下您的最核心依据（至少 1 条，随后点击下方按钮确认）：", key=f"rationale_{idx}", height=100)
                
                if len(rationale) > 0 and not st.session_state[f"pure_think_captured_{idx}"]:
                    st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"pure_think_captured_{idx}"] = True
                
                # 💡 UX 优化：用明确的按钮替代 Ctrl+Enter
                if len(rationale.strip()) < 5:
                    st.info("💡 请在上方填写依据（不少于 5 个字），随后确认解锁决策。")
                    decision = None
                else:
                    if not st.session_state.get(f"rationale_locked_{idx}", False):
                        if st.button("🔒 确认依据并解锁决策选项"):
                            st.session_state[f"rationale_locked_{idx}"] = True
                            st.rerun()
                    
                    if st.session_state.get(f"rationale_locked_{idx}", False):
                        st.success("✅ 依据已确认，请执行决策：")
                        decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                    else:
                        decision = None
            else:
                decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                rationale = "N/A (Control)"
                
                if decision != "(请选择)" and not st.session_state[f"pure_think_captured_{idx}"]:
                    st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"pure_think_captured_{idx}"] = True
            
            if decision and decision != "(请选择)" and decision != st.session_state[f"last_recorded_dec_{idx}"]:
                elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 倾向: {decision}")
                if st.session_state[f"last_recorded_dec_{idx}"] is not None:
                    st.session_state[f"change_count_{idx}"] += 1
                st.session_state[f"last_recorded_dec_{idx}"] = decision
            
            if decision and decision != "(请选择)":
                confidence = st.slider("决策信心 (1=极其犹豫，10=绝对确信)", 1, 10, 5, key=f"conf_{idx}")
                
                if st.button("提交本次项目审批", type="primary"):
                    total_reaction = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"action_log_{idx}"].append(f"[{total_reaction}s] 成功提交")
                    
                    st.session_state.results.append({
                        "p_id": p['id'],
                        "display_order": idx + 1,
                        "is_faulty_ai": p['is_faulty'],
                        "user_decision": decision,
                        "confidence": confidence,
                        "rationale_text": rationale,
                        "total_reaction_s": total_reaction,
                        "pure_think_s": st.session_state[f"pure_think_s_{idx}"],
                        "change_count": st.session_state[f"change_count_{idx}"],
                        "viewed_data": st.session_state.get(f"viewed_data_{idx}", False),
                        "action_log": " | ".join(st.session_state[f"action_log_{idx}"])
                    })
                    
                    if idx + 1 < len(st.session_state.active_projects):
                        st.session_state.current_p_idx += 1
                        st.rerun()
                    else:
                        st.session_state.step = "survey"
                        st.rerun()

# --- 步骤 4：复盘调研与数据入库 ---
elif st.session_state.step == "survey":
    st.title("✅ 沙盘推演完成！")
    st.success("感谢您的专业研判。为了帮助我们校准研究数据，请回答最后 4 个极其简短的问题。")
    
    with st.form("final_survey"):
        st.markdown("##### 调研回溯")
        k_p1 = st.select_slider(
            "1. 针对 P1 项目：您对**【中国信保的兜底机制】**熟悉程度如何？", 
            options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"]
        )
        k_p2 = st.select_slider(
            "2. 针对 P2 项目：您对**【欧盟 CBAM 碳关税】**熟悉程度如何？", 
            options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"]
        )
        
        # 💡 新增控制变量调研
        k_external = st.radio(
            "3. 在本次决策过程中，您是否查阅了外部资料（如搜索引擎、相关法规）？", 
            ["完全没有，仅凭经验与直觉", "查阅了少许资料核实", "查阅了大量资料进行比对"]
        )
        k_reliance = st.slider(
            "4. 总体而言，您认为自己在多大程度上依赖了 AI 的建议？\n(1=完全无视AI，10=完全听从AI)", 
            1, 10, 5
        )
        
        feedback = st.text_area("5. 有什么想对实验设计者说的？(选填)")
        
        if st.form_submit_button("封存数据并查看真相", type="primary"):
            final_payload = {
                "user_profile": st.session_state.user_data,
                "decisions": st.session_state.results,
                "survey": {
                    "knowledge_sinosure": k_p1, 
                    "knowledge_cbam": k_p2, 
                    "external_search": k_external,
                    "ai_reliance": k_reliance,
                    "feedback": feedback
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.final_payload = final_payload
            st.session_state.step = "finish"
            st.rerun()

# --- 步骤 5：感谢页与真相揭晓 ---
elif st.session_state.step == "finish":
    st.balloons()
    st.title("🎉 感谢您的参与！")
    st.markdown("您的所有决策数据已成功加密封存。您现在可以关闭本页面。")
    
    with st.expander("揭晓真相 (本项研究的真实目的)"):
        st.markdown("""
        **本研究旨在探究高压商业环境下的“人机交互与信任偏差”：**
        * **项目1 (信保)**：AI 实际上产生了**幻觉 (Automation Bias 测试)**。它过度放大了 5% 的微观敞口，试图掩盖信保能够 75% 兜底的宏观安全垫。如果您看破了底牌并推翻了 AI，恭喜您，您的理性战胜了算法恐吓！
        * **项目2 (绿氢)**：AI 给出了**真知 (Algorithm Aversion 测试)**。35% 的利润是诱饵，不足 10% 成功率的绿证抵扣是死胡同。如果您克制住了贪婪，顺从了 AI 的预警，说明您具备顶级的合规风险嗅觉！
        """)
    # 💡 移除了代码和后台 JSON 的输出
