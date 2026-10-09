import {SceneDirector} from '../flow/SceneDirector';
import type {ScriptData} from '../flow/types';
import {ThreeRoomView} from '../rendering/ThreeRoomView';
import {colors,ids} from '../domain/World';
export class PlaybackPanel {
  readonly viewport:HTMLElement;
  readonly overlay:HTMLElement;
  private director?:SceneDirector;
  constructor(root:HTMLElement,private script:ScriptData){
    root.innerHTML=`
      <header><div class="brand"><span class="brand-mark">SF</span><div>StageFlow<small>末日学校 · 舞台预演</small></div></div><div class="header-note">v5 原文 / 9 人 / 单房间</div></header>
      <main><section class="stage"><div class="stage-toolbar"><span class="stage-title">站位与互动</span><nav><button data-view="director" class="selected">导演视角</button><button data-view="top">俯视</button><button data-view="player">玩家视角</button></nav></div>
      <div id="viewport"><div id="labels"></div><div class="compass">N ↑<small>北门 / 演绎区</small></div><div class="canvas-note">拖动旋转 · 滚轮缩放<span>玩家视角会隐藏闭幕后的人物与气泡</span></div></div>
      <div class="transport"><div><button id="prev" title="上一步">←</button><button id="play" class="primary">播放</button><button id="next" title="下一步">→</button><button id="replay">重播本条</button></div><select id="speed" aria-label="速度"><option value="1">1× 速度</option><option value="1.5">1.5× 速度</option><option value="2">2× 速度</option></select></div>
      <div class="progress-row"><input type="range" id="progress" min="0" max="0" value="0" aria-label="条目进度"><span id="count"></span></div><div class="legend" id="legend"></div></section>
      <aside><div class="eyebrow">互动流程</div><select id="chapter" aria-label="环节"></select><div class="entry-line"><span id="entry-id"></span><span id="kind"></span></div><h1 id="chapter-title"></h1><div id="entry-text"></div>
      <div id="responses" hidden><div class="wait-heading">等待玩家回应</div><p>选择仅表示演示反应，原稿没有固定玩家台词。</p><button data-response="点头回应">示例：点头回应</button><button data-response="提出自己的意见">示例：提出意见</button><button data-response="暂不回应">示例：暂不回应</button></div>
      <div class="status" id="status"></div><details><summary>场地适配与使用说明</summary><p>本稿以玩家已坐好开场。北门供 NPC 入场，南门供玩家进出。新场地幕布横贯全宽，首位 NPC 出场时提前开幕；后续公共互动保持开幕，人物从中央通道到玩家区。</p><p>完整保留 v5 十个环节的台词、动作说明与编号。3D 走位是排练示意。下一步会执行本条走位，动作结束后停留；自动播放到玩家入口会等待。</p><p>已预留逐条音频接口，本版没有配音。示意房间非实测尺寸。</p></details></aside></main>`;
    this.viewport=root.querySelector('#viewport')!;this.overlay=root.querySelector('#labels')!;
    const legend=root.querySelector('#legend')!;
    for(const id of ids){const item=document.createElement('span');item.style.setProperty('--actor',colors[id]);item.textContent=id;legend.append(item);}
    const chapter=root.querySelector('#chapter')!;
    script.scenes.forEach((s,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=String(i+1).padStart(2,'0')+' · '+s.title;chapter.append(option);});
  }
  bind(director:SceneDirector,view:ThreeRoomView){
    this.director=director;const byId=(id:string)=>document.getElementById(id)!;
    byId('play').onclick=()=>{director.playing?director.pause():director.play();this.render();};
    byId('prev').onclick=()=>director.previous();byId('next').onclick=()=>director.next();byId('replay').onclick=()=>director.replay();
    (byId('speed') as HTMLSelectElement).onchange=e=>director.speed=Number((e.target as HTMLSelectElement).value);
    (byId('progress') as HTMLInputElement).max=String(director.beats.length-1);
    (byId('progress') as HTMLInputElement).oninput=e=>{director.pause();director.jump(Number((e.target as HTMLInputElement).value));};
    (byId('chapter') as HTMLSelectElement).onchange=e=>{director.pause();director.jump(director.beats.findIndex(b=>b.scene===Number((e.target as HTMLSelectElement).value)));};
    document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view.setCamera(b.dataset.view as 'director'|'top'|'player');document.querySelectorAll('[data-view]').forEach(el=>el.classList.toggle('selected',el===b));this.render();});
    document.querySelectorAll<HTMLButtonElement>('[data-response]').forEach(b=>b.onclick=()=>director.respond(b.dataset.response!));
    this.render();
  }
  render(){
    const d=this.director;if(!d)return;const beat=d.beat,scene=this.script.scenes[beat.scene];const id=(s:string)=>document.getElementById(s)!;
    id('play').textContent=d.playing?'暂停':'播放';id('count').textContent=(d.index+1)+' / '+d.beats.length;
    (id('progress') as HTMLInputElement).value=String(d.index);(id('chapter') as HTMLSelectElement).value=String(beat.scene);
    id('entry-id').textContent=beat.entry.id;id('kind').textContent=beat.speaker?beat.speaker+' · 台词':beat.entry.label;
    id('chapter-title').textContent=scene.title;id('entry-text').textContent=beat.entry.text.replace(/〔(G|N[1-4]|P[1-4])[^〕]*〕/g,'$1');
    id('responses').hidden=!d.waiting;id('status').textContent=d.waiting?'等待回应 · 可选示例，也可直接下一步':d.playing?'正在演示 · 随时暂停':'已暂停 · 阅读本条或继续';
  }
}
