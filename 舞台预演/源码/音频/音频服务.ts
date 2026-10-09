export class AudioService {
  private element?:HTMLAudioElement;
  get busy(){return !!this.element&&!this.element.paused&&!this.element.ended;}
  play(url?:string) {this.stop();if(!url)return;this.element=new Audio(url);void this.element.play().catch(()=>this.stop());}
  pause(){this.element?.pause();}
  resume(){if(this.element&&!this.element.ended)void this.element.play().catch(()=>this.stop());}
  stop(){this.element?.pause();this.element=undefined;}
}
