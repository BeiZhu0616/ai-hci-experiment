# -*- coding: utf-8 -*-

import datetime
import json
import random
import time
import uuid

import pandas as pd
import streamlit as st

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    GSheetsConnection = None


st.set_page_config(
    page_title="商业决策实验",
    layout="centered",
)


# --- 0. 基础校验函数 ---
def check_rationale_quality(text):
    text = text.strip()

    if len(text) == 0:
        return False, "请输入支撑您研判的核心依据。"

    if len(text) < 8:
        return False, "字数太少，请至少用一句完整中文说明理由。"

    if text.isdigit():
        return False, "请勿输入纯数字，请使用清晰的文字描述。"

    if len(set(text)) <= 2 and len(text) >= 3:
        return False, "包含过多重复无意义字符，请认真填写。"

    blacklist = [
        "不知道", "没有", "无", "如题", "同上", "随便", "测试",
        "没意见", "AI是对的", "同意", "信息不足", "11111",
        "asdf", "sdf", "qwer", "test", "hello"
    ]
    if any(word.lower() in text.lower() for word in blacklist):
        return False, "请提供具体的业务或技术依据，避免使用无意义词汇。"

    chinese_chars = sum("\u4e00" <= ch <= "\u9fff" for ch in text)
    if chinese_chars < 6:
        return False, "请使用中文说明您的核心判断依据。"

    business_keywords = [
        "风险", "收益", "现金流", "合规", "成本", "供应商", "信保",
        "赔付", "碳", "关税", "认证", "回款", "敞口", "政策",
        "市场", "客户", "融资", "合同", "违约"
    ]

    if not any(k in text for k in business_keywords):
        return False, "请结合项目中的业务、财务、合规或技术因素说明理由。"

    return True, ""


# --- 1. 项目库 ---
UNIVERSAL_PROJECTS = [
    {
        "id": "P1",
        "internal_metadata": {
            "domain": "Finance",
            "expert_dept": ["风险管理/合规部", "财务/资金管理部"]
        },
        "title": "东南亚光伏电站 EPC 项目授信决策",
        "detail": """**核心商业目标**

公司拟承接 T 国 100MW 光伏电站 EPC 总包项目，合同金额约 1.2 亿美元。该项目被视为公司进入当地新能源市场的重要样板工程。

**交易结构与内部意见**

商务条件为：业主支付 10% 预付款，剩余 90% 按工程节点支付，存在一定 O/A 账期。
业务开发部和工程部认为，该项目有助于公司打开区域市场，但也提示该国金融体系相对不成熟，历史上存在项目回款延迟的情况。

**当前决策**

请结合当前页面提供的信息与您的专业判断，决定是否批准该项目进入合同谈判阶段。""",
        "raw_data": """- **业主背景**：业主为当地较有影响力的能源集团，过往有大型基础设施项目履约记录，但近一年现金流波动明显。
- **财务变化**：业主母公司流动性指标有所下降，速动比率偏低，显示短期偿债能力承压；但其仍持有长期购电协议以及部分可抵押资产。
- **风险缓释安排**：公司已获得出口信用保险机构的原则性承保意向，可覆盖较大比例的商业信用风险，但具体赔付仍需满足报损、责任认定等条件。
- **历史经验**：类似国家项目中，曾出现“形式上符合承保条件，但在实际理赔中因单据或责任界定问题延迟或部分拒赔”的案例。
- **资金占用特征**：EPC 项目在施工阶段存在较高资金占用，一旦回款延迟，公司需承担阶段性现金流压力。""",
        "ai_advice": """**最终建议**：高风险，建议暂缓推进

**系统置信度**：92.4%

**Agent 推理链**

1. **流动性风险上升**：业主母公司流动性指标下降，说明其短期偿债能力减弱，工程款支付存在不确定性。
2. **保险保障存在执行不确定性**：信用保险虽能覆盖部分风险，但实际赔付依赖责任认定与流程，不能视为即时回款保障。
3. **资金占用风险**：在 EPC 项目中，账期叠加潜在回款延迟，可能对公司现金流形成压力，因此建议暂缓推进。""",
        "is_faulty": True
    },
    {
        "id": "P2",
        "internal_metadata": {
            "domain": "Tech",
            "expert_dept": ["工程技术中心", "新能源事业部"]
        },
        "title": "中东绿氢项目电解槽采购决策",
        "detail": """**核心商业目标**

公司拟推进中东绿氢项目投建，需采购 100MW 电解槽系统。该设备采购将直接影响项目初始投资额、交付进度和后续市场认证。

**供应链方案与内部意见**

经寻源，欧洲某供应商报价较市场均价低约 30-35%，且承诺交期提前约 2 个月。
采购部认为该报价有助于显著降低 CAPEX 并提升项目 IRR；工程部认为其性能满足要求。
但合规团队提示，该供应商生产端碳足迹较高，可能影响项目未来的绿色认证与部分市场准入。

**当前决策**

请结合当前页面提供的信息与您的专业判断，决定是否批准该采购合同。""",
        "raw_data": """- **设备性能**：该供应商为欧洲知名厂商，电解槽核心性能测试达标，报价较市场均价低约 30-35%，交付周期较短。
- **生产端碳足迹**：其主要产线位于东欧某国，电力结构中化石能源占比较高，单位制造碳排放强度高于部分西欧供应商。
- **政策环境**：欧盟 CBAM 仍处于过渡阶段，未来碳价水平、适用范围及核算方法仍存在不确定性，不同机构预测差异较大。
- **市场差异**：当前部分中东项目更关注成本与交付周期，对供应链碳足迹要求相对宽松；但欧洲客户及部分金融机构已开始强化相关要求。
- **潜在影响**：若项目未来面向欧盟客户或绿色融资渠道，供应链碳强度可能影响认证、融资条件或市场准入。""",
        "ai_advice": """**最终建议**：存在中长期合规风险，建议暂缓批准

**系统置信度**：91.8%

**Agent 推理链**

1. **短期成本优势明显**：该供应商报价和交付周期具有显著优势，有助于降低 CAPEX 并提升项目回报。
2. **中长期合规不确定性**：生产端碳排放较高，在未来面向欧盟客户或绿色融资环境下，可能带来额外成本或认证压力。
3. **风险不可完全对冲**：相关政策仍在演变，当前低成本优势未必能覆盖未来潜在的合规与市场准入风险，因此建议暂缓批准并进一步评估。""",
        "is_faulty": False
    }
]


# --- 2. 状态初始化 ---
def init_state():
    defaults = {
        "step": "consent_intro",
        "current_idx": 0,
        "user_data": {},
        "decisions": [],
        "active_projects": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def prepare_anonymous_experiment():
    if not st.session_state.user_data:
        st.session_state.user_data = {
            "id": f"ANON-{str(uuid.uuid4())[:6].upper()}",
            "organization": "Not collected",
            "department": "Not collected",
            "job_function": "Not collected",
            "management_level": "Not collected",
            "decision_role": "Not collected",
            "experience_years": None,
            "education": "Not collected",
            "enterprise_type": "Not collected",
            "gender": "Not collected",
            "birth_year": None,
            "ai_usage": "Not collected",
            "group": random.choice(["control", "treatment"]),
        }

    if not st.session_state.active_projects:
        projects = UNIVERSAL_PROJECTS.copy()
        random.shuffle(projects)
        st.session_state.active_projects = projects

    st.session_state.current_idx = 0
    st.session_state.decisions = []
    st.session_state.page_start_time = time.time()


init_state()


# --- 3. Consent + Intro Page ---
if st.session_state.step == "consent_intro":
    st.title("在线商业决策实验")

    st.markdown("### 一、研究介绍")
    st.markdown(
        """
本研究由西交利物浦大学研究团队开展。

研究关注人在 AI 辅助决策场景中的判断过程。

实验没有标准答案，也没有对错之分；请根据您的真实理解作答。
"""
    )

    st.markdown("### 二、参与说明")
    st.markdown(
        """
- 预计用时：5-8 分钟
- 任务内容：阅读项目情境和 AI 建议，并做出决策
- 系统会记录交互行为，包括点击、停留时间和决策结果
- 本实验不收集可识别个人身份的信息
- 本实验不涉及绩效评价
"""
    )

    st.markdown("### 三、知情同意")
    consent_read = st.checkbox("我已阅读并理解以上说明。", key="consent_read")
    consent_voluntary = st.checkbox("我确认自愿参与本实验。", key="consent_voluntary")
    consent_recording = st.checkbox("我同意系统记录本次实验中的交互行为和决策数据。", key="consent_recording")
    consent_anonymous = st.checkbox("我理解数据将匿名处理，提交后无法撤回。", key="consent_anonymous")
    consent_participate = st.checkbox("我同意开始参与本次实验。", key="consent_participate")

    all_consented = all([
        consent_read,
        consent_voluntary,
        consent_recording,
        consent_anonymous,
        consent_participate,
    ])

    if st.button("Start Experiment", type="primary", disabled=not all_consented, use_container_width=True):
        prepare_anonymous_experiment()
        st.session_state.step = "experiment"
        st.rerun()


# --- 4. 实验环节 ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx

    if not active_projects:
        prepare_anonymous_experiment()
        st.rerun()

    is_treatment_group = st.session_state.user_data["group"] == "treatment"

    if idx < len(active_projects):
        p = active_projects[idx]
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 {idx + 1}/{len(active_projects)}：{p['title']}")

        if f"tracker_init_{idx}" not in st.session_state:
            st.session_state[f"first_view_data_time_{idx}"] = None
            st.session_state[f"first_rationale_input_time_{idx}"] = None
            st.session_state[f"first_decision_time_{idx}"] = None
            st.session_state[f"last_recorded_dec_{idx}"] = None
            st.session_state[f"decision_change_count_{idx}"] = 0
            st.session_state[f"validation_block_count_{idx}"] = 0
            st.session_state[f"action_log_{idx}"] = []
            st.session_state[f"final_decision_{idx}"] = None
            st.session_state[f"tracker_init_{idx}"] = True

        with st.container(border=True):
            st.info(p["detail"])

            if not st.session_state.get(f"ai_called_{idx}", False):
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("我已初步审阅，申请 Agent 介入辅助研判", type="primary", use_container_width=True, key=f"ai_assist_{idx}"):
                    st.session_state[f"ai_called_{idx}"] = True
                    st.session_state[f"first_decision_time_{idx}"] = time.time()
                    st.session_state[f"action_log_{idx}"].append("[0.0s] 呼叫AI")
                    st.rerun()
            else:
                st.markdown("### Agent 深度研判报告")
                if p["is_faulty"]:
                    st.error(p["ai_advice"])
                else:
                    st.warning(p["ai_advice"])

                st.markdown("---")

                if not st.session_state.get(f"viewed_data_{idx}", False):
                    if st.button("查看补充资料", key=f"view_data_{idx}"):
                        st.session_state[f"viewed_data_{idx}"] = True

                        if st.session_state[f"first_view_data_time_{idx}"] is None:
                            st.session_state[f"first_view_data_time_{idx}"] = time.time()

                        elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 查阅底牌")
                        st.session_state[f"ui_refresh_{idx}"] = time.time()
                        st.rerun()
                else:
                    st.success("底层尽调参数已调取：")
                    with st.container(border=True):
                        st.markdown(p["raw_data"])

                st.markdown("---")
                st.markdown("### 做出您的最终决策")

                rationale = ""
                current_decision = None

                if is_treatment_group:
                    st.markdown("**第一步：列明您的核心决策依据（必填）**")
                    rationale = st.text_area(
                        "在做出最终决策前，请基于您目前掌握的所有资料，写下支撑您研判的最核心依据：",
                        key=f"rationale_{idx}",
                        height=100,
                    )

                    if len(rationale) > 0 and st.session_state[f"first_rationale_input_time_{idx}"] is None:
                        st.session_state[f"first_rationale_input_time_{idx}"] = time.time()
                        elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 开始撰写理由")

                    if not st.session_state.get(f"rationale_locked_{idx}", False):
                        if st.button("确认依据并解锁决策选项", key=f"confirm_rationale_{idx}"):
                            is_valid, error_msg = check_rationale_quality(rationale)
                            if not is_valid:
                                st.session_state[f"validation_block_count_{idx}"] += 1
                                current_offset = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                                st.session_state[f"action_log_{idx}"].append(f"[{current_offset}s] 拦截:{error_msg[:4]}")
                                st.error(error_msg)
                            else:
                                st.session_state[f"rationale_locked_{idx}"] = True
                                st.rerun()

                    if st.session_state.get(f"rationale_locked_{idx}", False):
                        st.success("依据校验通过，请执行决策：")
                        current_decision = st.radio(
                            "请选择：",
                            ["(请选择)", "批准项目", "否决项目"],
                            key=f"radio_{idx}",
                            horizontal=True,
                        )

                        if current_decision != "(请选择)":
                            st.session_state[f"final_decision_{idx}"] = current_decision
                else:
                    current_decision = st.radio(
                        "请选择：",
                        ["(请选择)", "批准项目", "否决项目"],
                        key=f"radio_{idx}",
                        horizontal=True,
                    )
                    rationale = "N/A (Control)"

                    if current_decision != "(请选择)" and st.session_state[f"first_rationale_input_time_{idx}"] is None:
                        st.session_state[f"first_rationale_input_time_{idx}"] = time.time()

                    if current_decision != "(请选择)":
                        st.session_state[f"final_decision_{idx}"] = current_decision

                final_decision = st.session_state.get(f"final_decision_{idx}")
                _ = st.session_state.get(f"ui_refresh_{idx}")

                last = st.session_state.get(f"last_recorded_dec_{idx}")
                if current_decision is not None and current_decision != "(请选择)" and current_decision != last:
                    elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 选:{current_decision[:2]}")
                    if last is not None:
                        st.session_state[f"decision_change_count_{idx}"] += 1
                    st.session_state[f"last_recorded_dec_{idx}"] = current_decision

                if final_decision:
                    conf = st.slider("决策信心评分 (1-10)：", 1, 10, 5, key=f"conf_{idx}")

                    if st.button("提交决策并继续", type="primary", key=f"submit_decision_{idx}"):
                        final_time = time.time()
                        base_time = st.session_state.get(f"first_decision_time_{idx}")
                        v_time = st.session_state.get(f"first_view_data_time_{idx}")
                        i_time = st.session_state.get(f"first_rationale_input_time_{idx}")

                        events = []
                        if base_time is not None:
                            events.append(("AI", base_time))
                        if v_time is not None:
                            events.append(("Info", v_time))
                        if i_time is not None:
                            events.append(("Reason", i_time))

                        order_labels = []
                        for name, t in sorted(events, key=lambda x: x[1]):
                            order_labels.append(f"{name}({round(t - base_time, 1)})" if base_time else name)

                        interaction_order = " -> ".join(order_labels)
                        interaction_order_simple = " -> ".join([name for name, _ in sorted(events, key=lambda x: x[1])])

                        non_ai_candidates = [t for t in [v_time, i_time] if t is not None]
                        pure_think_s = round(min(non_ai_candidates) - base_time, 2) if base_time and non_ai_candidates else None

                        total_dwell_time = final_time - st.session_state.page_start_time
                        total_reaction_time = final_time - st.session_state[f"first_decision_time_{idx}"]

                        expert_list = p["internal_metadata"]["expert_dept"]
                        current_dept = st.session_state.user_data["department"]
                        is_expert_match = 1 if current_dept in expert_list else 0

                        action_log_list = st.session_state[f"action_log_{idx}"]
                        first_choice_offset = None
                        final_choice_offset = None

                        for event in action_log_list:
                            if "选:" in event:
                                try:
                                    offset = float(event.split("]")[0].replace("[", "").replace("s", ""))
                                    if first_choice_offset is None:
                                        first_choice_offset = offset
                                    final_choice_offset = offset
                                except ValueError:
                                    pass

                        decision_made_offset = final_choice_offset
                        decision_made_time = base_time + final_choice_offset if base_time and final_choice_offset is not None else None
                        first_choice_time = base_time + first_choice_offset if base_time and first_choice_offset is not None else None
                        stabilization_time = (
                            round(decision_made_time - first_choice_time, 2)
                            if decision_made_time and first_choice_time
                            else None
                        )

                        pre_decision_behaviors = []
                        for event in action_log_list:
                            try:
                                event_offset = float(event.split("]")[0].replace("[", "").replace("s", ""))
                            except ValueError:
                                continue

                            if decision_made_offset is not None and event_offset >= decision_made_offset:
                                continue

                            if "呼叫AI" in event and "AI" not in pre_decision_behaviors:
                                pre_decision_behaviors.append("AI")
                            elif ("撰写理由" in event or "开始撰写" in event) and "Reason" not in pre_decision_behaviors:
                                pre_decision_behaviors.append("Reason")
                            elif ("查阅底牌" in event or "查阅" in event) and "Info" not in pre_decision_behaviors:
                                pre_decision_behaviors.append("Info")

                        interaction_order_clean = " -> ".join(pre_decision_behaviors) if pre_decision_behaviors else "N/A"

                        post_decision_info = 1 if (decision_made_time and v_time and v_time > decision_made_time) else 0
                        post_decision_info_strict = 1 if (v_time and decision_made_time and v_time > decision_made_time + 1.0) else 0
                        post_decision_info_delay_s = (
                            round(v_time - decision_made_time, 2)
                            if post_decision_info and decision_made_time and v_time
                            else None
                        )

                        st.session_state[f"action_log_{idx}"].append(f"[{round(total_reaction_time, 1)}s] 提交")

                        action_log_struct = []
                        for event in st.session_state[f"action_log_{idx}"]:
                            try:
                                time_str = event.split("]")[0].replace("[", "").replace("s", "")
                                relative_time = float(time_str)
                                event_desc = event.split("] ")[1] if "] " in event else event
                                action_log_struct.append({"t": relative_time, "event": event_desc})
                            except ValueError:
                                pass

                        row = {
                            "subject_id": st.session_state.user_data["id"],
                            "experiment_group": st.session_state.user_data["group"],
                            "organization": st.session_state.user_data["organization"],
                            "department": st.session_state.user_data["department"],
                            "job_function": st.session_state.user_data["job_function"],
                            "management_level": st.session_state.user_data["management_level"],
                            "decision_role": st.session_state.user_data["decision_role"],
                            "experience_years": st.session_state.user_data["experience_years"],
                            "education": st.session_state.user_data["education"],
                            "enterprise_type": st.session_state.user_data["enterprise_type"],
                            "gender": st.session_state.user_data["gender"],
                            "birth_year": st.session_state.user_data["birth_year"],
                            "ai_usage": st.session_state.user_data["ai_usage"],
                            "is_expert_match": is_expert_match,
                            "p_id": p["id"],
                            "display_order": idx + 1,
                            "is_faulty_ai": p["is_faulty"],
                            "user_decision": 1 if final_decision == "批准项目" else 0,
                            "confidence": conf,
                            "rationale_text": rationale,
                            "total_dwell_s": round(total_dwell_time, 2),
                            "pure_think_s": pure_think_s,
                            "total_reaction_s": round(total_reaction_time, 2),
                            "change_count": st.session_state[f"decision_change_count_{idx}"],
                            "block_count": st.session_state[f"validation_block_count_{idx}"],
                            "viewed_data": st.session_state.get(f"viewed_data_{idx}", False),
                            "view_to_input_gap_s": (
                                round(abs(i_time - v_time), 2)
                                if (v_time is not None and i_time is not None)
                                else None
                            ),
                            "action_log": " -> ".join(st.session_state[f"action_log_{idx}"]),
                            "action_log_list": json.dumps(st.session_state[f"action_log_{idx}"], ensure_ascii=False),
                            "action_log_struct": json.dumps(action_log_struct, ensure_ascii=False),
                            "interaction_order": interaction_order,
                            "interaction_order_simple": interaction_order_simple,
                            "interaction_order_clean": interaction_order_clean,
                            "interaction_order_pre": interaction_order_clean,
                            "interaction_order_full": interaction_order,
                            "post_decision_info": post_decision_info,
                            "post_decision_info_strict": post_decision_info_strict,
                            "post_decision_info_delay_s": post_decision_info_delay_s,
                            "stabilization_time": stabilization_time,
                            "decision_commit_time": first_choice_time,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }

                        st.session_state.decisions.append(row)
                        st.session_state.current_idx += 1
                        st.session_state.page_start_time = time.time()
                        st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()


# --- 5. 复盘调研与数据保存 ---
elif st.session_state.step == "survey":
    st.title("实验复盘")
    st.caption("最后一步，请根据刚才的实际体验作答。")

    with st.form("survey_form"):
        behavior_text = st.radio(
            "1. 在刚才的决策过程中，您是否查阅了外部资料？",
            ["完全没有，仅凭经验和直觉", "偶尔查阅了基础常识", "深度验证了核心信息"],
        )

        trust_text = st.select_slider(
            "2. AI 的建议对您最终决策的影响程度：",
            options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"],
        )

        know_p1_text = st.select_slider(
            "3. 您对出口信用保险承保与理赔机制的熟悉程度：",
            options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"],
            key="k_p1",
        )

        know_p2_text = st.select_slider(
            "4. 您对欧盟 CBAM 碳关税对供应链影响的熟悉程度：",
            options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"],
            key="k_p2",
        )

        feedback = st.text_area("5. 有什么想补充的意见？（选填）")

        behavior_map = {
            "完全没有，仅凭经验和直觉": 0,
            "偶尔查阅了基础常识": 1,
            "深度验证了核心信息": 2,
        }
        trust_map = {"无影响": 1, "轻微参考": 2, "中立": 3, "显著影响": 4, "决定性影响": 5}
        knowledge_map = {"完全陌生": 1, "略知一二": 2, "具备基础概念": 3, "比较熟悉": 4, "极其精通": 5}

        if st.form_submit_button("提交数据", type="primary"):
            for d in st.session_state.decisions:
                d.update({
                    "search_behavior": behavior_map[behavior_text],
                    "trust_level": trust_map[trust_text],
                    "knowledge_sinosure": knowledge_map[know_p1_text],
                    "knowledge_cbam": knowledge_map[know_p2_text],
                    "feedback": feedback,
                })

            saved_to_gsheets = False
            if GSheetsConnection is not None:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        existing_data = conn.read(worksheet="Sheet1", ttl=0)
                        existing_data = existing_data.dropna(how="all")
                    except Exception:
                        existing_data = pd.DataFrame()

                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    saved_to_gsheets = True
                except Exception as exc:
                    st.session_state["save_error"] = str(exc)

            if not saved_to_gsheets:
                st.session_state["local_results"] = pd.DataFrame(st.session_state.decisions).to_csv(index=False)

            st.session_state.step = "debrief"
            st.rerun()


# --- 6. 完成页 ---
elif st.session_state.step == "debrief":
    st.title("实验已完成")
    st.success("感谢您的参与。您的回答已提交。")

    if "local_results" in st.session_state:
        st.info("云端同步未启用或暂不可用。本次数据已保存在当前会话中，可在下方下载。")
        st.download_button(
            "下载本次数据",
            data=st.session_state["local_results"],
            file_name=f"experiment_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
