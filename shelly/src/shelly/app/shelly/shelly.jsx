define(
  ['react', 'react-mdl', 'react-router', 'websocket','telldus','shelly/config'],
  function(React, ReactMDL, ReactRouter, WebSocket, Telldus, ShellyConfig) {
  
    Telldus.loadCSS('/pluginloader/plugins.css');
    Telldus.loadCSS('/shelly/style/shelly.css');
    
    class ShellyApp extends React.Component {
      constructor(props) {
        super(props);
        this.state = {'devices': null}
        this.websocket = new WebSocket();
      }
      componentDidMount() {
        this.websocket.onMessage('shelly', 'refresh', (module, action, data) => {
            console.log(data);
            this.setState(data)
        });
        fetch('/shelly/list')
          .then(response => response.json())
          .then(json => this.setState({'devices': json.devices,
                                       'ver' : json.ver,
                                       'id': json.id,
                                       'pyShellyVer' : json.pyShellyVer }))
      }
      componentWillUnmount() {
        this.websocket.onMessage('shelly', 'status', null);
      }
      sendCmd(id, cmd, e) {
          e.preventDefault();
          fetch('/shelly/' + cmd + '?id=' + id)
      }
      addMember(e) {
          e.preventDefault();
          fetch('/shelly/addMember')
      }
      dropMember(e) {
          e.preventDefault();
          fetch('/shelly/dropMember')
      }
      clean(e) {
          e.preventDefault();
          fetch('/shelly/clean')
      }
      initSocket(e) {
          e.preventDefault();
          fetch('/shelly/initSocket')
      }
      discover(e) {
          e.preventDefault();
          fetch('/shelly/discover')
      }
      pickColor(id, e) {
        this.selectedId = id;
        var pos = this.getPos(e.target);
        
        var picker = document.getElementById('picker');
        var canvas = document.getElementsByClassName("ShellyCanvas")[0].parentElement
        picker.style.display = "block";
        picker.style.top = Math.min(canvas.offsetHeight + canvas.scrollTop - 300, pos[1]-50+canvas.scrollTop);        
        picker.style.left = Math.max(pos[0]-300, 10);
        var ctx = picker.getContext('2d');

        var image = new Image();        
        image.onload = function () {
            ctx.drawImage(image, 0, 0, image.width, image.height);
        }
        image.src = "/shelly/img/colorwheel.png"
        
        document.addEventListener('mousedown', this.outsidePick);
      }
      outsidePick(e) {
        var canvas = document.getElementById('picker');
        if (e==null || !canvas.contains(event.target)) {
            document.removeEventListener('mousedown', this.handleClickOutside);
            canvas.style.display = "none"; 
            //this.selectedId = 0;
        }
      }
      getPos(el) {
        var x = 0;
        var y = 0;        
        while( el && !isNaN( el.offsetLeft ) && !isNaN( el.offsetTop ) ) {
            x += el.offsetLeft - el.scrollLeft;
            y += el.offsetTop - el.scrollTop;
            el = el.offsetParent;
        }
        return [x, y]
      }
      //toHex(c) {
      //    var hex = c.toString(16);
      //    return hex.length == 1 ? "0" + hex : hex;
      //} 
      selectColor(e) {
      
        var canvas = document.getElementById('picker');
        var ctx = canvas.getContext('2d');
        
        var pos = this.getPos(e.target);
        
        var canvasX = Math.floor(e.pageX - pos[0]);
        var canvasY = Math.floor(e.pageY - pos[1]);

        // get current pixel
        var imageData = ctx.getImageData(canvasX, canvasY, 1, 1);
        var pixel = imageData.data;

        //this.setState( state => {
        //    state.devices.find(d=>d.id==this.selectedId).changingColorTo 
        //                        = '#'+this.toHex(pixel[0])+this.toHex(pixel[1])+this.toHex(pixel[2])
        //    return {devices: state.devices};
        //});
        
        fetch("/shelly/rgb?id="+this.selectedId+"&r="+pixel[0]+"&g="+pixel[1]+"&b="+pixel[2] )
        this.outsidePick();
      }
      rename(id, oldName, e) { 
          e.preventDefault();
          var newName = prompt("Enter new name", oldName);
          if (newName != null)
            fetch('/shelly/rename?id=' + id + '&name=' + newName)
      }
      configure(e) { 
        e.preventDefault();
        this.refs.configDlg.open()
      }
      renderValues(dev) { 
        var values = {};
        sensors = dev.sensors || {}
        if (sensors['consumption'])
            values['consumption']=sensors['consumption'] + "W";
        if (sensors['temp'])
            values['temp']=sensors['temp'] + "\u00B0C";
        if (sensors['hum'])
            values['hum']=sensors['hum'] + "%";
        if (dev.brightness) {
            values['brght']=Math.round(dev.brightness) + "%";
        }
        return <div className="values">{Object.entries(values)
                     .map(([key, value])=><span key={key} className="value">{value}</span>)}</div>;
      }
      render() {
          const { devices, ver, pyShellyVer, id } = this.state;
          return (           
           <div className="shellyCanvas">  
            <table><tbody>
                <tr>
                    <td className="head"></td>
                    <td>
                      <table className="info-table"><tbody>
                        <tr><td>Version:</td><td>{ver} (pyShelly: {pyShellyVer})</td></tr>
                        <tr><td>Telldus id:</td><td>{id}</td></tr>
                        <tr><td>Cloud API:</td><td><a onClick={(e)=>this.configure(e)}>Configure</a></td></tr>
                      </tbody></table>
                    </td>
                </tr>
            </tbody></table>
            {/*
            <ReactMDL.Button onClick={(e) => this.clean(e)}>Clean</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.discover(e)}>Discover</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.initSocket(e)}>Init socket</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.addMember(e)}>Add member</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.dropMember(e)}>Drop member</ReactMDL.Button>
            */}
            { devices &&
            <table className="list"><tbody>
              <tr><th></th><th></th><th>Name</th><th>IP address</th><th></th><th></th><th>Upgrade</th></tr>
              {devices.map(dev =>
                <tr key={dev.id} className={!dev.available ? "unavailable" : "available"}>                  
                  <td>
                    { dev.available && dev.isDevice &&                        
                        <img src={"/shelly/img/state_" + (dev.state==2?2:1) + ".png"}></img>
                    }
                    { dev.available && dev.rgb && dev.state==16 &&
                        <div onClick={(e) => this.pickColor(dev.id, e)}
                            className="rgb" style={{backgroundColor:dev.rgb}}></div>
                    }
                  </td>
                  <td>
                    { this.renderValues(dev) }
                  </td>
                  <td>
                    <div>{dev.name}</div>
                    <div className="type_name">
                      {dev.params.typeName} - {dev.params.firmwareVersion}
                    </div></td>                  
                  <td><a href={"http://" + dev.params.ipAddr} target="_blank">{dev.params.ipAddr}</a></td>
                  <td className={"button_row " + (!dev.available ? "hide" : "")}>
                    { dev.buttons.on &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "turnon", e)}>
                      <img src={"/shelly/img/btn_action_1.png"}></img>
                    </ReactMDL.Button>}
                    { dev.buttons.off &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "turnoff", e)}>
                      <img src={"/shelly/img/btn_action_2.png"}></img>
                    </ReactMDL.Button>}
                    { dev.buttons.up &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "up", e)}>
                      <img src={"/shelly/img/btn_action_128.png"}></img>
                    </ReactMDL.Button>}
                    { dev.buttons.down &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "down", e)}>
                      <img src={"/shelly/img/btn_action_256.png"}></img>
                    </ReactMDL.Button>}
                    { dev.buttons.stop &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "stop", e)}>
                      <img src={"/shelly/img/btn_action_512.png"}></img>
                    </ReactMDL.Button>}                    
                    </td>
                   <td>
                    <ReactMDL.Button onClick={(e) => this.rename(dev.id, dev.name, e)}>Rename</ReactMDL.Button>
                  </td>
                  <td>                    
                    {dev.buttons.firmware &&
                    <ReactMDL.Button title="Click to upgrade to latest firmware" onClick={(e) => this.sendCmd(dev.id, "firmware_update", e)}>
                      {dev.params.latestFwVersion}
                    </ReactMDL.Button>}
                  </td>
                </tr>
              )}
            </tbody></table>
            }                
            <canvas id="picker" width="300" height="300" onClick={(e) => this.selectColor(e)}></canvas>
            <ShellyConfig ref="configDlg"/>
           </div>
          );
      }
    };

  return ShellyApp;
  }
);
