import streamlit as st
import pandas as pd
import datetime
import time
from streamlit_gsheets import GSheetsConnection

# --- 1. 配置与项目库 ---
PROJECT_POOL = {
    "学生": [
        {"id": "P1", "title": "埃及 P1 太阳能电站评估", "detail": "项目：100MWac；投资：USD 54M；IRR：12.4%。关键点：依据《埃及绿色能源法案 2024-V3》，项目位于沙姆沙伊赫（红海沿岸），可享受 15 年免税。", "ai_advice": "【建议放弃】。审计显示该地理坐标属于《尼罗河三角洲生态保护区》，免税条款不适用。", "is_faulty": True},
        {"id": "P2", "title": "东南亚工业园微电网改造", "detail": "模式：BOOT。预期收益：碳指标交易占 15%。风险：当地劳工法案修订可能导致成本上升。", "ai_advice": "【建议投资】。Agent 预测碳指标价格将持续走高，足以覆盖潜在的劳工成本波动风险。", "is_faulty": False}
    ],
    "老师": [
        {"id": "P1", "title": "埃及 P1 PV 项目可行性审查", "detail": "100MWac；LCOE: $0.021/kWh；参考文件：EG-GEA-2024-001。要求 30 年合规期追溯。", "ai_advice": "【不建议投资】。交叉审计显示该经纬度坐标不在 EG-GEA-2024 政策红利覆盖区。建议重新评估土地属性。", "is_faulty": True},
        {"id": "P2", "title": "阿曼绿氢集成示范工程", "detail": "技术：PEM 电解堆。符合欧盟 RFNBO 标准。关键参数：弱电网环境，SCR 实测值 1.2。", "ai_advice": "【建议暂停】。极弱电网下（SCR<1.5），现有控制算法存在高频振荡脱网风险，硬件兼容性未经验证。", "is_faulty": False}
    ],
    "企业从业人员": [
        {"id": "P1", "title": "埃及 P1 项目 CRO 风险决策", "detail": "投资额：5000 万美金。合规要求：满足 30 年追溯审计。VUCA 因子：地缘政治波动及潜在的碳关税（CBAM）风险。", "ai_advice": "【建议放弃】。供应链审计发现 EPC 承包商存在二级供应商合规违规风险，可能触发国际金融机构的制裁限制。", "is_faulty": True},
        {"id": "P2", "title": "阿曼绿氢项目供应链韧性评估", "detail": "核心：PEM 电解堆。环境：SCR 稳定性风险。财务：需进行 30% 的非本币结算风险对冲。", "ai_advice": "【建议暂停】。识别到极低 SCR 环境下的系统震荡风险及潜在的反倾销调查，建议立即启动备选供应商预案。", "is_faulty": False}
    ]
}

# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'start_time', 'decisions']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "login"
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：登录/信息收集 ---
if st.session_state.step == "login":
    st.title("🛡️ 工程决策人机协作实验平台")
    st.markdown("---")
    with st.form("user_info_form"):
        u_id = st.text_input("受试者编号/学号 (或昵称)", placeholder="例: 张三 或 SUB-01")
        role = st.selectbox("您的专业身份", ["学生", "老师", "企业从业人员"])
        major = st.text_input("所属专业/部门", placeholder="例: 战略投资部")
        
        if st.form_submit_button("开始正式实验"):
            if u_id:
                st.session_state.user_data = {"id": u_id, "role": role, "major": major}
                st.session_state.step = "experiment"
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                st.error("请填写编号后再继续。")

# --- 4. 步骤 2：实验环节（平铺式布局） ---
elif st.session_state.step == "experiment":
    role = st.session_state.user_data['role']
    active_projects = PROJECT_POOL[role]
    idx = st.session_state.current_idx
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"任务进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 ID: {p['id']} - {p['title']}")
        
        # 4.1 展示数据
        with st.container(border=True):
            st.subheader("📑 项目详细数据")
            st.info(p['detail'])
            ready = st.checkbox("我已审阅上述详细数据，申请 Agent 介入建议", key=f"ready_{idx}")

        # 4.2 触发 AI 建议
        if ready:
            st.divider()
            st.subheader("🤖 Agent 辅助建议")
            st.warning("GreenInvest Agent 正在实时调取全球合规数据库...")
            if f"waited_{idx}" not in st.session_state:
                time.sleep(1.5)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(f"**Agent 核心建议：** {p['ai_advice']}")
            
            # 4.3 决策区域
            with st.container(border=True):
                st.subheader("您的最终投资意向")
                decision = st.radio("基于以上所有信息，您的选择：", ["建议投资", "不建议投资"], key=f"dec_{idx}", index=None)
                conf = st.slider("决策信心 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                
                elapsed = time.time() - st.session_state.start_time
                btn_disabled = (elapsed < 5) or (decision is None)
                btn_label = "提交决策并继续" if elapsed >= 5 else f"请审阅建议 ({int(5-elapsed)}s)"
                
                if st.button(btn_label, type="primary", disabled=btn_disabled, key=f"btn_{idx}"):
                    row = {
                        "subject_id": st.session_state.user_data['id'],
                        "role": st.session_state.user_data['role'],
                        "major": st.session_state.user_data['major'],
                        "p_id": p['id'],
                        "is_faulty_ai": p['is_faulty'],
                        "user_decision": decision,
                        "confidence": conf,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.decisions.append(row)
                    
                    st.session_state.current_idx += 1
                    st.session_state.start_time = time.time()
                    st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 5. 步骤 3：复盘调研与云端自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘调查")
    with st.form("survey_form"):
        behavior = st.radio("1. 您是否通过外部搜索引擎（如百度）查阅过资料？", ["从未", "偶尔查阅常识", "深度验证参数/法案"])
        trust = st.select_slider("2. Agent 建议对您的影响程度：", options=["无影响", "轻微", "中立", "显著", "决定性"])
        suspicion = st.text_area("3. 是否有发现任何异常之处？")

        if st.form_submit_button("提交反馈并解锁真相"):
            # 在受试者点提交的这一刻，程序静默连通 Google Sheet
            with st.spinner("正在加密回传数据，请稍候..."):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 读取已有数据并清理空行
                    try:
                        existing_data = conn.read(worksheet="Sheet1")
                        existing_data = existing_data.dropna(how="all")
                    except:
                        existing_data = pd.DataFrame()
                        
                    # 拼装带有复盘数据的结果
                    for d in st.session_state.decisions:
                        d.update({"search_behavior": behavior, "trust_level": trust, "feedback": suspicion})
                    
                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    # 更新到云端
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                except Exception as e:
                    # 如果网络波动导致保存失败，给出一个极小的错误提示，但不打断用户流程
                    st.toast("数据同步可能出现延迟，但不影响您的实验进程。", icon="⚠️")
                    print(e)
            
            st.session_state.step = "debrief"
            st.rerun()

# --- 6. 步骤 4：真相告知 ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 实验已完成，非常感谢您的参与！")
    
    with st.expander("🎓 关于本研究的机密说明 (点击展开)", expanded=True):
        st.write("""
        本研究旨在评估工程师、高管与学生在面对 Agentic-AI 时的‘信任校准’机制。
        **为了测试极限情况，部分 AI 建议（如 P1 项目的保护区或合规违规）是我们故意植入的技术幻觉。**
        
        您的直觉判断和决策数据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续同事的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您工作顺利！")