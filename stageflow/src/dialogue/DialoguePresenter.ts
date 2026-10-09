import type {ActorId} from '../domain/World';
import {ids,colors} from '../domain/World';
import {ThreeRoomView} from '../rendering/ThreeRoomView';
export class DialoguePresenter {
  private names=new Map<ActorId,HTMLElement>();
  private bubble=document.createElement('div');
  private speaker?:ActorId;
  private expires=0;
  get activeSpeaker(){return this.speaker;}
  constructor(private view:ThreeRoomView,container:HTMLElement){
    for(const id of ids){const tag=document.createElement('div');tag.className='actor-tag';tag.textContent=id;tag.style.setProperty('--actor',colors[id]);container.append(tag);this.names.set(id,tag);}
    this.bubble.className='speech-bubble';container.append(this.bubble);
  }
  set(speaker:ActorId|undefined,text:string,example=false){
    this.speaker=speaker;this.expires=0;this.bubble.replaceChildren();
    if(speaker){const title=document.createElement('strong');title.textContent=example?speaker+' · 演示回应':speaker;const p=document.createElement('p');p.textContent=text.replace(/〔(G|N[1-4]|P[1-4])[^〕]*〕/g,'$1');this.bubble.append(title,p);this.bubble.style.setProperty('--actor',colors[speaker]);}
  }
  response(actor:ActorId,text:string){this.set(actor,text,true);this.expires=performance.now()+2400;}
  update(){
    for(const [id,tag] of this.names){const at=this.view.project(id);tag.hidden=!at.onScreen||!this.view.isVisible(id);tag.style.left=at.x+'px';tag.style.top=at.y+'px';tag.classList.toggle('speaking',id===this.speaker);}
    if(this.expires&&performance.now()>this.expires){this.speaker=undefined;this.expires=0;}
    if(!this.speaker){this.bubble.hidden=true;return;}
    const at=this.view.project(this.speaker);this.bubble.hidden=!this.view.isVisible(this.speaker)||!at.onScreen;
    this.bubble.style.left=Math.max(158,Math.min(this.view.container.clientWidth-158,at.x))+'px';this.bubble.style.top=Math.max(140,at.y-22)+'px';
  }
}
