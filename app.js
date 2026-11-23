const $ = (id) => document.getElementById(id);
let donors = [], editingId = null, toastTimer;
const palette = ["#df4350","#e9874d","#4778df","#7a68c8","#1a9b79","#d4a13a","#4d9eae","#a0a9b8"];
const api = async (url, options={}) => {
  const response = await fetch(url, {headers:{"Content-Type":"application/json", ...(options.headers||{})}, ...options});
  const data = await response.json().catch(()=>({error:"Unexpected server response"}));
  if(!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
};
function notify(message){const el=$("toast");el.textContent=message;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),3000)}
function esc(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function localDate(){const d=new Date();return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)}
async function load(){
  try{
    const [records,stats]=await Promise.all([api("/api/donors"),api("/api/summary")]);
    donors=records; renderRows(); renderStats(stats.summary,stats.warnings); renderCharts(stats.summary);
  }catch(e){notify(e.message)}
}
function renderStats(s,warnings){
  $("totalStat").textContent=s.total;$("donatedStat").textContent=s.donated;$("ageStat").textContent=s.total?s.average_age:"—";
  $("overdueStat").textContent=s.overdue;$("donationRate").textContent=`${s.donation_rate}% completion rate`;
  $("warnings").innerHTML=warnings.map(w=>`<div class="warning ${w.level==="info"?"info":""}">⚑ &nbsp;${esc(w.message)}</div>`).join("");
}
function renderRows(){
  const q=$("searchInput").value.toLowerCase(), group=$("groupFilter").value, status=$("statusFilter").value;
  const list=donors.filter(d=>(!q||[d.name,d.id,d.phone,d.city,d.blood_group].join(" ").toLowerCase().includes(q))&&(!group||d.blood_group===group)&&(!status||d.status===status));
  $("recordCount").textContent=`${list.length} of ${donors.length} records`;
  $("donorRows").innerHTML=list.length?list.map(d=>`<tr>
    <td><span class="donor-name">${esc(d.name)}</span><span class="donor-id">${esc(d.id)}</span></td>
    <td><span class="blood-badge">${esc(d.blood_group)}</span></td><td>${esc(d.age)}</td><td>${esc(d.city)}</td><td>${esc(d.camp_date)}</td>
    <td><span class="status-badge ${esc(d.status)}">${esc(d.status)}</span></td>
    <td><button class="action-btn" title="Edit registration" data-edit="${esc(d.id)}">✎</button><button class="action-btn" title="Delete registration" data-delete="${esc(d.id)}">⌫</button></td></tr>`).join(""):`<tr><td colspan="7" class="empty">No matching registrations found.</td></tr>`;
}
function renderCharts(s){
  const canvas=$("bloodChart"),ctx=canvas.getContext("2d"),groups=Object.entries(s.blood_groups),total=s.total;
  const width=canvas.clientWidth||500,height=canvas.clientHeight||205,ratio=window.devicePixelRatio||1;
  canvas.width=width*ratio;canvas.height=height*ratio;ctx.scale(ratio,ratio);ctx.clearRect(0,0,width,height);
  $("chartEmpty").style.display=total?"none":"grid";
  const max=Math.max(1,...groups.map(x=>x[1])),left=28,right=8,top=13,bottom=29,plotH=height-top-bottom,plotW=width-left-right;
  ctx.font="10px DM Sans";ctx.textAlign="right";ctx.fillStyle="#9aa5b3";ctx.strokeStyle="#edf0f4";ctx.lineWidth=1;
  for(let i=0;i<=4;i++){let y=top+plotH*i/4;ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(width-right,y);ctx.stroke();ctx.fillText(String(Math.round(max*(4-i)/4)),left-8,y+3)}
  let step=plotW/groups.length,bw=Math.min(24,step*.55);
  groups.forEach(([g,v],i)=>{let h=plotH*v/max,x=left+i*step+(step-bw)/2,y=top+plotH-h;ctx.fillStyle=palette[i];ctx.beginPath();ctx.roundRect(x,y,bw,Math.max(0,h),[4,4,0,0]);ctx.fill();ctx.fillStyle="#778499";ctx.textAlign="center";ctx.fillText(g,left+i*step+step/2,height-9)});
  $("groupLegend").innerHTML=groups.filter(x=>x[1]).map(([g,v],i)=>`<span><i style="background:${palette[groups.findIndex(x=>x[0]===g)]}"></i>${g} <b>${v}</b></span>`).join("");
  $("statusBars").innerHTML=Object.entries(s.statuses).map(([name,count])=>`<div class="status-row"><span>${name}</span><div class="track"><div class="fill" style="width:${total?count/total*100:0}%"></div></div><b>${count}</b></div>`).join("");
}
function openModal(record=null){
  editingId=record?.id||null;$("donorForm").reset();$("formError").textContent="";
  $("modalTitle").textContent=record?"Edit registration":"Register a donor";
  $("saveDonorBtn").textContent=record?"Update registration":"Save registration";
  const f=$("donorForm");
  if(record) Object.entries(record).forEach(([k,v])=>{if(f.elements[k])f.elements[k].value=v});
  else {f.elements.camp_date.value=localDate();f.elements.status.value="Registered"}
  $("donorModal").hidden=false;f.elements.name.focus();
}
function closeModal(){$("donorModal").hidden=true;editingId=null}
$("newDonorBtn").addEventListener("click",()=>openModal());
$("closeModal").addEventListener("click",closeModal);$("cancelModal").addEventListener("click",closeModal);
$("donorModal").addEventListener("click",e=>{if(e.target===$("donorModal"))closeModal()});
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal()});
$("donorForm").addEventListener("submit",async e=>{
  e.preventDefault();$("formError").textContent="";
  const payload=Object.fromEntries(new FormData(e.currentTarget).entries());
  try{
    await api(editingId?`/api/donors/${encodeURIComponent(editingId)}`:"/api/donors",{method:editingId?"PUT":"POST",body:JSON.stringify(payload)});
    closeModal();await load();notify(editingId?"Registration updated":"Donor registered successfully");
  }catch(err){$("formError").textContent=err.message}
});
$("donorRows").addEventListener("click",async e=>{
  const edit=e.target.closest("[data-edit]"),del=e.target.closest("[data-delete]");
  if(edit){const r=donors.find(x=>x.id===edit.dataset.edit);if(r)openModal(r)}
  if(del){const r=donors.find(x=>x.id===del.dataset.delete);if(r&&confirm(`Delete registration for ${r.name} (${r.id})?`)){
    try{await api(`/api/donors/${encodeURIComponent(r.id)}`,{method:"DELETE"});await load();notify("Registration deleted")}catch(err){notify(err.message)}
  }}
});
["searchInput","groupFilter","statusFilter"].forEach(id=>$(id).addEventListener(id==="searchInput"?"input":"change",renderRows));
$("refreshBtn").addEventListener("click",load);
$("todayLabel").textContent=new Date().toLocaleDateString(undefined,{weekday:"long",day:"numeric",month:"long",year:"numeric"});
$("exportBtn").addEventListener("click",async()=>{
  try{const r=await api("/api/reports");const names=[...r.files,...(r.chart?[r.chart]:[])];$("exportResult").innerHTML="Reports ready — download:<br>"+names.map(n=>`<a href="/download/${encodeURIComponent(n)}">${esc(n)}</a>`).join("<br>")+(r.chart?"":"<br>Matplotlib not installed; interactive dashboard chart is available.");notify("Reports generated")}
  catch(e){$("exportResult").textContent=e.message}
});
$("csvFile").addEventListener("change",async e=>{
  const file=e.target.files[0];if(!file)return;
  try{const csv=await file.text();const result=await api("/api/import",{method:"POST",body:JSON.stringify({csv})});
    $("importResult").innerHTML=`Imported: <b>${result.imported}</b> · Rejected: <b>${result.errors.length}</b>`+(result.errors.length?`<br>`+result.errors.slice(0,12).map(x=>`Row ${x.row}: ${esc(x.error)}`).join("<br>"):"");
    await load();notify("CSV import completed");
  }catch(err){$("importResult").textContent=err.message}
  e.target.value="";
});
window.addEventListener("resize",()=>api("/api/summary").then(r=>renderCharts(r.summary)).catch(()=>{}));
load();
