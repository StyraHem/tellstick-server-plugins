define(
  ['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'websocket', 'telldus'],
  function(React, ReactMDL, ReactRedux, DialogPolyfill, WebSocket, Telldus) {
  
    class ShellyConfig extends React.Component {
      constructor() {
        super();
        this.state = {
          visible: false,
          cloud_server : "",
          cloud_auth_key : ""
        }
      }

      componentDidMount() {
      }

      handleChange(e) {
        this.setState({ [e.target.name]: e.target.value })
      }
      
      save() {
        fetch('/shelly/config?cloud_server=' + this.state.cloud_server + '&cloud_auth_key=' + this.state.cloud_auth_key)
          .then(response => response.json())
          .then(json => this.setState(json))
        this.setState({'visible': false})
      }
      
      open() {        
        fetch('/shelly/config')
          .then(response => response.json())
          .then(json => this.setState(json))
          .then(this.setState({'visible': true}))
      }

      close() {
        this.setState({'visible': false})
        //this.props.onSave(this.props.plugin.name, this.state.values)
      }

      render() {
         return (
           <ReactMDL.Dialog open={this.state.visible} ref={(c)=>this.dialog=c} style={{width: 700, padding: '0'}}>
             <ReactMDL.DialogTitle>
              Shelly Cloud API
             </ReactMDL.DialogTitle>
             <ReactMDL.DialogContent>
             <div>
                 <h5>Instructions</h5>
                 Enter the cloud API information here so the plugin can get the name of the devices from Shelly Cloud.<br/>
                 - Get this this information from <a target="_blank" href="https://my.shelly.cloud/#user_settings">Shelly Cloud</a> (click).<br/>
                 - Under <b>Security</b> and <b>AUTORISATION CLOUD KEY</b> click <b>GET KEY</b>.<br/>
                 - Enter server and key below and save.<br/><br/>
               </div>
                <ReactMDL.Textfield
                  autofocus 
                  onChange={(e) => this.handleChange(e)}
                  floatingLabel
                  label = 'Cloud server'
                  placeholder = ''
                  name = 'cloud_server'
                  value = {this.state.cloud_server}
                />
                <ReactMDL.Textfield
                  onChange={(e) => this.handleChange(e)}
                  style={{width: 500}}
                  rows={2}
                  floatingLabel
                  label = 'Cloud authentication key'
                  name = 'cloud_auth_key'
                  value = {this.state.cloud_auth_key}
                  placeholder = ''
                />
             </ReactMDL.DialogContent>
             <ReactMDL.DialogActions style = {{ padding: '12px'}}>
               <ReactMDL.Button type = 'button' className="buttonRounded buttonAccept" raised onClick={() => this.save()}>Save</ReactMDL.Button>
               <ReactMDL.Button type='button' className="buttonRounded buttonWhite" raised onClick={() => this.close()}>Close</ReactMDL.Button>
             </ReactMDL.DialogActions>
           </ReactMDL.Dialog>
        )
      }
    }
  
    // ShellyConfig.propTypes = {
    //   plugin: React.PropTypes.object,
    // };
    // const mapStateToProps = (state) => ({
    //   //plugin: state.plugins.find((plugin) => (plugin.name == state.configure)) || {name: '', config: {}, category: 'other', color: '#757575'},
    //   show: state.configure !== null,
    // });
    // const mapDispatchToProps = (dispatch) => ({
    //   onSave: (plugin, values) => dispatch(Actions.saveConfiguration(plugin, values)),
    //   onClose: () => dispatch(Actions.ShellyConfig(null)),
    // });

    return ShellyConfig; //ReactRedux.connect(mapStateToProps, mapDispatchToProps)(ShellyConfig);
  }
);
