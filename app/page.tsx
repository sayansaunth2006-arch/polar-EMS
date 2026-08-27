import { Activity, ArrowUpRight, CheckCircle2, ChevronRight, Clock3, HeartPulse, MapPin, Radio, ShieldCheck, Signal, Users } from "lucide-react";

const capabilities = [
  { icon: Radio, title: "Live fleet visibility", text: "See every unit, crew, and response status in one calm operational view." },
  { icon: HeartPulse, title: "Clinical handoff", text: "Keep patient context moving securely from dispatch to destination." },
  { icon: ShieldCheck, title: "Built for trust", text: "Role-based access, audit trails, and resilient workflows by default." },
];

export default function Home() {
  return (
    <main>
      <nav className="nav container" aria-label="Primary navigation">
        <a className="brand" href="#top"><span className="brand-mark"><Activity size={18} /></span><span>polar<span className="brand-dot">.</span>EMS</span></a>
        <div className="nav-links"><a href="#platform">Platform</a><a href="#workflow">Workflow</a><a href="#security">Security</a></div>
        <a className="nav-cta" href="#contact">Request a demo <ArrowUpRight size={16} /></a>
      </nav>

      <section className="hero container" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><span className="pulse-dot" /> Emergency operations, made clear</div>
          <h1>Move care forward.<br /><em>Without the noise.</em></h1>
          <p className="hero-text">polar.EMS gives emergency medical teams the live picture they need to make faster, safer decisions when every minute matters.</p>
          <div className="hero-actions"><a className="button primary" href="#contact">See polar.EMS in action <ChevronRight size={17} /></a><a className="text-link" href="#platform">Explore the platform <ArrowUpRight size={15} /></a></div>
          <div className="trusted"><span>Trusted by teams who operate</span><div className="trusted-logos"><b>Northstar</b><b>MED<span>+</span></b><b>HARBOR / 24</b></div></div>
        </div>
        <div className="hero-visual" aria-label="Live operations dashboard preview">
          <div className="dashboard-glow" />
          <div className="dashboard-card">
            <div className="dash-top"><div><span className="live-label"><span className="pulse-dot" /> LIVE OPERATIONS</span><h2>Tuesday, 14 May <small>08:42:16</small></h2></div><button className="icon-button" aria-label="Dashboard options">•••</button></div>
            <div className="dash-stats"><div><span>ACTIVE UNITS</span><strong>24</strong><small className="positive">+3 available</small></div><div><span>IN RESPONSE</span><strong>08</strong><small>2 priority calls</small></div><div><span>AVG. ARRIVAL</span><strong>07:42</strong><small className="positive">↓ 12% this week</small></div></div>
            <div className="map-panel"><div className="map-grid" /><div className="route route-one" /><div className="route route-two" /><div className="map-pin pin-one"><MapPin size={15} /></div><div className="map-pin pin-two"><MapPin size={15} /></div><div className="map-pin pin-three"><MapPin size={15} /></div><div className="map-center"><span className="radar" /><Signal size={15} /></div><div className="map-label label-one">Unit 14 <small>En route</small></div><div className="map-label label-two">St. Agnes ER <small>ETA 04 min</small></div></div>
            <div className="activity-row"><div className="unit-avatar">14</div><div><b>Unit 14 dispatched</b><span>Cardiac response · West District</span></div><span className="activity-time">2 min ago</span><CheckCircle2 className="check" size={17} /></div>
          </div>
        </div>
      </section>

      <section className="metrics container"><div><strong>99.98%</strong><span>platform uptime</span></div><div><strong>42 sec</strong><span>dispatch to acknowledgement</span></div><div><strong>18k+</strong><span>responses coordinated</span></div><div><strong>24/7</strong><span>operational support</span></div></section>

      <section className="platform-section" id="platform"><div className="container"><div className="section-heading"><div><span className="kicker">ONE OPERATIONAL PICTURE</span><h2>Clarity for the moments<br /><em>that matter most.</em></h2></div><p>From first call to final handoff, polar.EMS connects the people, information, and decisions that keep care moving.</p></div><div className="capability-grid">{capabilities.map(({ icon: Icon, title, text }) => <article className="capability" key={title}><div className="cap-icon"><Icon size={19} /></div><h3>{title}</h3><p>{text}</p><a href="#contact">Learn more <ArrowUpRight size={14} /></a></article>)}</div></div></section>

      <section className="workflow container" id="workflow"><div className="workflow-visual"><div className="workflow-line" /><div className="workflow-step active"><span>01</span><div><b>Dispatch receives the call</b><small>Location and priority captured instantly</small></div><Clock3 size={18} /></div><div className="workflow-step"><span>02</span><div><b>Best-fit unit is alerted</b><small>Availability, distance, and skill aligned</small></div><Users size={18} /></div><div className="workflow-step"><span>03</span><div><b>Care team stays connected</b><small>Live updates through arrival and handoff</small></div><CheckCircle2 size={18} /></div></div><div className="workflow-copy"><span className="kicker">DESIGNED AROUND YOUR TEAM</span><h2>Less coordinating.<br /><em>More caring.</em></h2><p>Every screen is designed to reduce cognitive load, surface the next right action, and give your team confidence under pressure.</p><a className="button secondary" href="#contact">How it works <ArrowUpRight size={16} /></a></div></section>

      <section className="security container" id="security"><div><span className="kicker">READY WHEN YOU ARE</span><h2>The calm inside<br />the <em>response.</em></h2></div><div className="security-note"><ShieldCheck size={22} /><p>Secure by design, simple by nature. polar.EMS fits the way your teams work today—and scales with where you&apos;re going next.</p><a href="#contact">Talk to our team <ArrowUpRight size={15} /></a></div></section>
      <footer className="footer container" id="contact"><a className="brand" href="#top"><span className="brand-mark"><Activity size={18} /></span><span>polar<span className="brand-dot">.</span>EMS</span></a><span>© 2026 polar.EMS</span><div><a href="#security">Privacy</a><a href="#security">Security</a><a href="mailto:hello@polar-ems.com">Contact</a></div></footer>
    </main>
  );
}
