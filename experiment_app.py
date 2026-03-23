import streamlit as st
import pandas as pd
import datetime
import os
import time

# --- 1. 配置与项目库（全虚构，含隐蔽陷阱） ---
PROJECT_POOL = {
    "学生": [
        {"id": "P1", "title": "埃及 P1 太阳能电站评估", "detail": "项目：100MWac；投资：USD 54M；IRR：12.4%。关键点：依据《埃及绿色能源法案 2024-V3》，项目位于沙姆沙伊赫（红海沿岸），可享受 15 年免税。", "ai_advice": "【建议放弃】。审计显示该地理坐标属于《尼罗河三角洲生态保护区》，法案规定的免税条款不适用于本区域，将增加 22% 的税收成本。", "is_faulty": True},
        {"id": "P2", "title": "东南亚工业园微电网改造", "detail": "模式：BOOT。预期收益：碳指标交易占 15%。风险：当地劳工法案修订可能导致成本上升。", "ai_advice": "【建议投资】。Agent 预测碳指标价格将持续走高，足以覆盖潜在的劳工成本波动风险。", "is_faulty": False}
    ],
    "老师": [
        {"id": "P1", "title": "埃及 P1 PV 项目可行性审查", "detail": "100MWac；LCOE: $0.021/kWh；参考文件：EG-GEA-2024-001。涉及跨国审计合规性，要求 30 年合规期追溯。", "ai_advice": "【不建议投资】。交叉审计显示该经纬度坐标不在 EG-GEA-2024 政策红利覆盖区。建议重新评估土地属性。", "is_faulty": True},
        {"id": "P2", "title": "阿曼绿氢集成示范工程", "detail": "技术：PEM 电解堆。符合欧盟 RFNBO 标准。关键参数：弱电网环境，SCR 实测值 1.2。", "ai_advice": "【建议暂停】。极弱电网下（SCR<1.5），现有逆变器控制算法存在高频振荡脱网风险，硬件兼容性未经验证。", "is_faulty": False}
    ],
    "企业从业人员": [
        {"id": "P1", "title": "埃及 P1 项目 CRO 风险决策", "detail": "投资额：5000 万美金。合规要求：满足 30 年追溯审计。VUCA 因子：地缘政治波动及潜在的碳关税（CBAM）风险。", "ai_advice": "【建议放弃】。供应链审计发现 EPC 承包商存在二级供应商合规违规风险，可能触发国际金融机构的制裁限制。", "is_faulty": True},
        {"id": "P2", "title": "阿曼绿氢项目供应链韧性评估", "detail": "核心：PEM 电解堆。环境：SCR 稳定性风险。财务：需进行 30% 的非本币结算风险对冲。", "ai_advice": "【建议暂停】。识别到极低 SCR 环境下的系统震荡风险及潜在的反倾销调查，建议立即启动备选供应商预案。", "is_faulty": False}
    ]
}

# --- 2. 状态初始化与防御性检查 ---
for key in ['step', 'current_idx', 'user_data', 'start_time', 'decisions']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "login"
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：收集背景信息 ---
if st.session_state.step == "login":
    st.title("🛡️ 工程决策人机协作实验平台")
    st.markdown("---")
    with st.form("user_info_form"):
        u_id = st.text_input("受试者编号/学号 (用于数据归档)", placeholder="例: SUB2026-01")
        role = st.selectbox("您的专业身份", ["学生", "老师", "企业从业人员"])
        major = st.text_input("所属专业/部门", placeholder="例: 管理科学与工程")
        
        if st.form_submit_button("开始正式实验"):
            if u_id:
                st.session_state.user_data = {"id": u_id, "role": role, "major": major}
                st.session_state.step = "experiment"
                st.session_state.start_time = time.time() # 初始化第一个任务的开始时间
                st.rerun()
            else:
                st.error("请填写受试者编号。")

# --- 4. 步骤 2：核心实验循环 ---
elif st.session_state.step == "experiment":
    role = st.session_state.user_data['role']
    active_projects = PROJECT_POOL[role]
    idx = st.session_state.current_idx
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.caption(f"任务进度: {idx+1} / {len(active_projects)}")
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 ID: {p['id']} - {p['title']}")
        
        tab1, tab2 = st.tabs(["📑 项目详细数据", "🤖 Agent 辅助建议"])
        
        with tab1:
            st.info(p['detail'])
            ready = st.checkbox("我已审阅上述详细数据，申请 Agent 介入建议", key=f"ready_{idx}")

        with tab2:
            if ready:
                st.warning("GreenInvest Agent 正在实时调取全球合规数据库...")
                time.sleep(1) # 增加仿真感
                st.error(f"**Agent 核心建议：** {p['ai_advice']}")
                
                with st.container(border=True):
                    decision = st.radio("您的最终投资意向：", ["建议投资", "不建议投资"], key=f"dec_{idx}")
                    conf = st.slider("您的决策信心 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                    
                    # 行为监控：强制阅读时间检查（5秒）
                    elapsed = time.time() - st.session_state.start_time
                    btn_label = "提交决策并继续" if elapsed >= 5 else f"请仔细审阅建议 ({int(5-elapsed)}s)"
                    
                    if st.button(btn_label, type="primary", disabled=(elapsed < 5)):
                        # 记录当前决策
                        current_row = {
                            "subject_id": st.session_state.user_data['id'],
                            "role": st.session_state.user_data['role'],
                            "p_id": p['id'],
                            "is_faulty_ai": p['is_faulty'],
                            "user_decision": decision,
                            "confidence": conf,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.decisions.append(current_row)
                        
                        # 翻页逻辑
                        st.session_state.current_idx += 1
                        st.session_state.start_time = time.time() # 重置下一个任务计时
                        st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 5. 步骤 3：实验后回顾性调研 (Post-Experiment Survey) ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘调查")
    st.markdown("在查看实验真相前，请协助我们完成最后的行为评估：")
    
    with st.form("survey_form"):
        search_behavior = st.radio(
            "1. 在决策过程中，您是否通过外部搜索引擎（如百度、谷歌）查阅过资料？",
            ["从未查阅，完全凭经验/AI建议", "偶尔查阅了基本常识", "深度查阅并验证了AI提到的法案/参数"]
        )
        trust_level = st.select_slider("2. 您主观感觉 Agent 的建议对您的影响程度：", options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"])
        suspicion = st.text_area("3. 您在实验中是否有任何怀疑或发现异常的地方？")

        if st.form_submit_button("提交反馈并解锁实验真相"):
            # 整合所有数据并保存
            final_df = pd.DataFrame(st.session_state.decisions)
            final_df['search_behavior'] = search_behavior
            final_df['subject_trust'] = trust_level
            final_df['feedback'] = suspicion
            
            save_path = "exp_results_full.csv"
            final_df.to_csv(save_path, mode='a', header=not os.path.exists(save_path), index=False, encoding='utf-8-sig')
            
            st.session_state.step = "debrief"
            st.rerun()

# --- 6. 步骤 4：真相告知 (Debriefing) ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 实验已顺利完成！")
    with st.expander("🎓 核心研究机密说明 (Debriefing)", expanded=True):
        st.write(f"""
        感谢您的参与，**{st.session_state.user_data['id']}**。
        本研究属于‘人机协同决策中的信任校准’实验。为了测量决策者对 AI 建议的依赖程度，我们在实验中设置了‘幻觉 Agent’。
        
        **真相揭秘：**
        - 在 P1 项目中，Agent 提供的‘尼罗河三角洲保护区’或‘制裁风险’是**编造的错误逻辑**。
        - 您的所有行为数据已成功回传，这将极大地帮助我们研究如何在未来的工程系统中构建‘可信 AI’。
        
        **请务必不要向后续可能的参与者透露此细节，以维持数据的科学性。**
        """)
    st.info("您可以安全地关闭此页面。祝您工作/学习愉快！")