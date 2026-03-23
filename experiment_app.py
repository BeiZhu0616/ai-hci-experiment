import streamlit as st
import pandas as pd
import datetime
import time
import random
from streamlit_gsheets import GSheetsConnection

# --- 1. 配置与项目库 ---
# --- 1. 配置与项目库 (高生态效度版) ---
PROJECT_POOL = {
    "学生": [
        {"id": "P1", "title": "埃及 P1 太阳能电站评估", 
         "detail": "【项目背景】本项目为位于埃及沙姆沙伊赫（红海省南端）的 100MWac 地面光伏电站。采用 N型 TOPCon 双面组件与平单轴跟踪支架，预计年等效利用小时数可达 2100 小时。\n【财务测算】静态总投资约 5400 万美元，资本金内部收益率（IRR）测算为 12.4%，静态投资回收期 7.2 年。\n【政策与合规】项目核心盈利点在于利用《埃及绿色能源法案 2024-V3》（EG-GEA-2024）。根据该法案，红海沿岸的新能源开发区可享受 15 年企业所得税免除及进口设备零关税。\n【当前进展】已取得当地政府的初步用地许可（环评报告编制中），EPC 总包招标已进入技术标评审阶段。", 
         "ai_advice": "【建议放弃】。审计显示该地理坐标属于《尼罗河三角洲生态保护区》，免税条款不适用。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "东南亚工业园微电网改造", 
         "detail": "【项目背景】位于东南亚某核心工业园区的源网荷储一体化微电网改造项目。涵盖 15MW 屋顶光伏、5MW/10MWh 磷酸铁锂储能及园区能源管理系统，采用 BOOT（建设-拥有-运营-移交）模式，特许经营期 20 年。\n【财务与收益】基准 IRR 为 10.8%。项目创新性地将绿电溢价与碳减排指标（CCER 类）交易纳入收益模型，预计碳资产收益将占总营收的 15% 以上。\n【风险评估】目前主要面临当地《新劳工法案》修订风险，可能导致运维期的本土人工成本上浮 10%-15%。\n【当前进展】已与园区管委会签订排他性意向协议，正在进行并网接入方案的审批。", 
         "ai_advice": "【建议投资】。Agent 预测区域碳指标价格将持续走高，超额收益足以完全覆盖潜在的劳工成本波动风险。", 
         "is_faulty": False}
    ],
    
    "老师": [
        {"id": "P1", "title": "埃及 P1 PV 项目可行性审查", 
         "detail": "【项目背景】埃及沙姆沙伊赫 100MWac 绿地光伏项目可行性审查。技术路线拟采用 210mm 大尺寸硅片及集中式逆变器方案，占地约 220 公顷，区域光照资源评估为 A 类。\n【技术经济指标】全生命周期平准化度电成本（LCOE）极具竞争力，测算值仅为 $0.021/kWh。P50 发电量下，项目资本金 IRR 达 12.8%。\n【合规与政策基准】财务模型高度依赖《埃及绿色能源法案 2024》（文件号：EG-GEA-2024-001）中的税收抵扣条款。法案要求项目用地必须明确属于“国家新能源特许开发区”，且需满足严苛的 30 年用地合规期追溯审计。\n【当前进展】可研报告已完成初稿，第三方律所已出具了初步的土地尽调备忘录（无重大瑕疵），正等待内部投委会过会。", 
         "ai_advice": "【不建议投资】。交叉审计显示该经纬度坐标不在 EG-GEA-2024 政策红利覆盖区。建议重新评估土地属性。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "阿曼绿氢集成示范工程", 
         "detail": "【项目背景】阿曼杜库姆（Duqm）经济特区绿氢集成示范工程。一期规划 50MW 风光互补制氢，核心制氢设备拟选用欧洲某一线品牌的 PEM（质子交换膜）电解槽。产品定位出口，符合欧盟 RFNBO（非生物来源可再生燃料）认证标准。\n【核心工程参数】项目所在区域属典型的沙漠边缘弱电网环境。前期电网接入点实测短路比（SCR）仅为 1.2，系统惯量极低。\n【财务与进度】预计总投资 1.2 亿美元，已获得阿曼主权基金的联合投资意向。目前正处于前端工程设计（FEED）阶段尾声。\n【技术挑战】风机、光伏逆变器与 PEM 电解槽电源的源网荷协调控制策略尚在仿真阶段，暂无当地电网调度的正式批复。", 
         "ai_advice": "【建议暂停】。极弱电网下（SCR<1.5），现有微网控制算法存在高频振荡脱网风险，核心硬件的工况兼容性未经验证。", 
         "is_faulty": False}
    ],
    
    "企业从业人员": [
        {"id": "P1", "title": "埃及 P1 项目 CRO 风险决策", 
         "detail": "【项目背景】埃及 P1 新能源项目（标的额：5000 万美元）的最终风险投资决策（CRO 视角）。项目采用有限追索权项目融资，融资杠杆率 75%，主要资金来源为某多边开发银行（MDB）。\n【核心商业条款】PPA（购电协议）期限 25 年，电价以美元结算，具备较强的抗通胀能力。预期全投资 IRR 为 10.5%。\n【VUCA 风险因子】当前面临两大不确定性：一是红海周边的地缘政治波动可能导致的保费上浮；二是未来绿电产品出口欧洲潜在的碳边境调节机制（CBAM）壁垒。\n【合规约束】MDB 资金方要求执行极其严格的 ESG 审计，特别是针对项目用地的 30 年产权追溯，以及要求核心 EPC 总包方提供全链路的供应链合规（无涉裁实体）承诺书。", 
         "ai_advice": "【建议放弃】。供应链审计发现拟定 EPC 承包商存在二级供应商合规违规风险，极大概率将触发国际金融机构的制裁限制。", 
         "is_faulty": True},
        
        {"id": "P2", "title": "阿曼绿氢项目供应链韧性评估", 
         "detail": "【商业背景】阿曼杜库姆绿氢项目供应链韧性及财务风险评估。项目核心卡脖子设备为大标方 PEM 电解堆，目前单一来源锁定欧洲供应商，交付周期长达 14 个月。项目 100% 承购协议（Offtake）已与某日韩财团初步锁定。\n【技术与供应链风险】工程团队反馈并网点存在极低短路比（SCR=1.2）的稳定性风险，可能导致电解堆频繁启停，加速组件衰减。此外，欧洲供应链近期受到航运危机影响，物流成本大幅上浮。\n【财务结构】资本支出（CAPEX）中约 30% 为非本币结算，存在较大的汇率敞口，需按季购买远期外汇合约（Forward）进行对冲。\n【当前进展】EPC 合同与核心设备采购合同（PO）均处于待签署状态，董事会要求在一周内出具最终风险意见。", 
         "ai_advice": "【建议暂停】。识别到极低 SCR 环境下的系统震荡风险及潜在的设备反倾销审查阻碍，建议立即启动备选供应商预案。", 
         "is_faulty": False}
    ]
}
# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "login"
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}

# --- 3. 步骤 1：登录/信息收集 ---
# --- 3. 步骤 1：登录/信息收集 ---
if st.session_state.step == "login":
    st.title("🛡️ 工程决策人机协作实验平台")
    
    # 🌟 新增的知情同意说明（使用 st.info 呈现漂亮的蓝色提示框）
    st.info("""
    **【科研知情同意说明】**\n
    欢迎参与本次学术研究！本研究旨在评估“新一代工业大模型（Agentic-AI）在复杂工程决策中的可用性与辅助效果”。\n
    * **您的任务：** 阅读 2 个模拟的海外工程项目摘要，参考 AI 给出的辅助建议，并做出您的最终投资判断。
    * **数据保密：** 您的决策数据将完全匿名化处理，仅用于学术统计分析，绝不涉及任何商业机密或个人隐私。
    * **自愿原则：** 您有权在任何时候中止本次实验。\n
    **填写下方信息并点击“开始正式实验”按钮，即表示您已知晓上述信息并同意参与。**
    """)
    
    st.markdown("---")
    with st.form("user_info_form"):
        u_id = st.text_input("受试者编号/学号 (或昵称)", placeholder="例: 张三 或 SUB-01")
        role = st.selectbox("您的专业身份", ["学生", "老师", "企业从业人员"])
        major = st.text_input("所属专业/部门", placeholder="例: 战略投资部")
        
        if st.form_submit_button("开始正式实验"):
            if u_id:
                st.session_state.user_data = {"id": u_id, "role": role, "major": major}
                
                # 随机打乱项目顺序 Counterbalancing
                projects = PROJECT_POOL[role].copy()
                random.shuffle(projects) 
                st.session_state.active_projects = projects
                
                st.session_state.step = "experiment"
                st.session_state.page_start_time = time.time()
                st.rerun()
            else:
                st.error("请填写编号后再继续。")

# --- 4. 步骤 2：实验环节（平铺式布局） ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
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
            # 【学术优化 2：精准记录 AI 暴露时间】
            if f"ai_reveal_time_{idx}" not in st.session_state:
                st.session_state[f"ai_reveal_time_{idx}"] = time.time()
                
            st.divider()
            st.subheader("🤖 Agent 辅助建议")
            st.warning("GreenInvest Agent 正在实时调取全球合规数据库...")
            
            # 仅在第一次显示建议时模拟延迟
            if f"waited_{idx}" not in st.session_state:
                time.sleep(1.5)
                st.session_state[f"waited_{idx}"] = True
            
            st.error(f"**Agent 核心建议：** {p['ai_advice']}")
            
            # 4.3 决策区域
            with st.container(border=True):
                st.subheader("您的最终投资意向")
                decision = st.radio("基于以上所有信息，您的选择：", ["建议投资", "不建议投资"], key=f"dec_{idx}", index=None)
                conf = st.slider("决策信心 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                
                # 强制停留逻辑（从看到 AI 建议开始算 5 秒）
                elapsed_since_reveal = time.time() - st.session_state[f"ai_reveal_time_{idx}"]
                btn_disabled = (elapsed_since_reveal < 5) or (decision is None)
                btn_label = "提交决策并继续" if elapsed_since_reveal >= 5 else f"请审阅建议 ({int(5-elapsed_since_reveal)}s)"
                
                if st.button(btn_label, type="primary", disabled=btn_disabled, key=f"btn_{idx}"):
                    # 计算两个关键时间
                    final_time = time.time()
                    total_dwell_time = final_time - st.session_state.page_start_time
                    ai_reaction_time = final_time - st.session_state[f"ai_reveal_time_{idx}"]
                    
                    # 记录这一轮的决策（注意：我们把文本选项转成了更容易做统计的数字 1 和 0）
                    row = {
                        "subject_id": st.session_state.user_data['id'],
                        "role": st.session_state.user_data['role'],
                        "major": st.session_state.user_data['major'],
                        "p_id": p['id'],
                        "is_faulty_ai": p['is_faulty'],
                        "user_decision": 1 if decision == "建议投资" else 0, # 数据预处理优化
                        "confidence": conf,
                        "total_dwell_s": round(total_dwell_time, 2), # 总浏览时间
                        "ai_reaction_s": round(ai_reaction_time, 2), # 纯看 AI 思考的时间
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.decisions.append(row)
                    
                    # 翻页与重置时钟
                    st.session_state.current_idx += 1
                    st.session_state.page_start_time = time.time()
                    st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()

# --- 5. 步骤 3：复盘调研与云端自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘调查")
    with st.form("survey_form"):
        # 同样做了数字编码优化，方便后续跑回归
        behavior_text = st.radio("1. 您是否通过外部搜索引擎查阅过资料？", ["从未", "偶尔查阅常识", "深度验证参数/法案"])
        trust_text = st.select_slider("2. Agent 建议对您的影响程度：", options=["无影响", "轻微", "中立", "显著", "决定性"])
        suspicion = st.text_area("3. 是否有发现任何异常之处？(选填)")
        
        # 映射字典
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
                        
                    # 把复盘结果注入到每一条决策记录中
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
