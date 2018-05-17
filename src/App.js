import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import './App.css';
import Plot from 'react-plotly.js';
import { FormGroup, InputGroup, Glyphicon, FormControl, ButtonToolbar, Button, Panel, Row, Col } from 'react-bootstrap';
import Interweave from 'interweave';
import dropzoneStyles from './dropzone-styles';


class SearchForm extends React.Component {
  render() {
    return (
      <form>
        <FormGroup>
            <InputGroup>
      <InputGroup.Addon>
        <Glyphicon glyph="search"/>
      </InputGroup.Addon>
            <FormControl
        type="text"
            value={this.props.value}
            placeholder="Subject search"
            onChange={this.props.handleChange}
        />
            </InputGroup>
        </FormGroup>
      </form>
    );
  }
}


class ClearSelectedButton extends React.Component {
    constructor(props, context) {
        super(props, context);
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        console.log('Clear selection!');
        this.props.handleClearSelection();
    }

    render() {
        return (
                <Button
            bsStyle="primary"
            disabled={this.props.disabled}
            onClick={!this.props.disabled ? this.handleClick : null}
                >
                Clear
            </Button>
        );
    }
}

class ExportSelectedButton extends React.Component {
    constructor(props, context) {
        super(props, context);
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        console.log('Export selection!');
        this.props.handleExportSelection();
    }

    render() {
        return (
                <Button
            bsStyle="primary"
            disabled={this.props.disabled}
            onClick={!this.props.disabled ? this.handleClick : null}
                >
                Export
            </Button>
        );
    }
}

class Infobox extends React.Component {
    render() {
        return (
                <Panel>
                <Panel.Body>
                  <Interweave tagName="div" content={this.props.text} />
                </Panel.Body>
                </Panel>
        );
    }
}

class PlotlyApp extends React.Component {
    constructor(props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
        this.onClick = this.onClick.bind(this);
        this.onSelect = this.onSelect.bind(this);
        this.onHover = this.onHover.bind(this);
        this.onInitialized = this.onInitialized.bind(this);
        this.onUpdate = this.onUpdate.bind(this);
    }

    handleChange(e) {
        this.props.onDataChange(e.target.value);
    }

    onClick(e) {
        this.props.onClick(e);
    }

    onSelect(e) {
        console.log('Select!', e);
    }

    onInitialized(figure) {
        console.log('onInitialized!', figure);
    }

    onUpdate(figure) {
        // console.log('onUpdate!', figure);
        this.props.onUpdate(figure);
    }

    onHover(e) {
        this.props.onHover(e);
    }

    render() {
        return (
            <Plot
                data={this.props.data}
                layout={this.props.layout}
                frames={this.props.frames}
                onClick={this.onClick}
                onSelect={this.onSelect}
            onHover={this.onHover}
            // onInitialized={(figure) => this.setState(figure)}
            // onUpdate={(figure) => this.setState(figure)}
            // onInitialized={(figure) => this.onInitialized(figure)}
            onUpdate={(figure) => this.onUpdate(figure)}
            config={this.props.config}
            useResizeHandler={true}
            style={{
                width: '100%',
                height: '100%',
            }}
            />
        );
    }
}


class FileDrop extends React.Component {
    constructor() {
        super();
        this.state = { files: [] };
    }

    onDrop(files) {
        this.setState({
            files
        });

        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = () => {
                const data = JSON.parse(reader.result);
                this.props.onDataChange(data);
            };
            reader.onabort = () => console.log('file reading was aborted');
            reader.onerror = () => console.log('file reading has failed');

            reader.readAsText(file);
        });
    }

    render() {
        return (
                <section>
                  <div className="dropzone">
                <Dropzone
            style={dropzoneStyles.default}
            activeStyle={dropzoneStyles.active}
            rejectStyle={dropzoneStyles.rejected}
            multiple={false}
            onDrop={this.onDrop.bind(this)}>
                <p>
                Drag a JSON BLAST file here, or click to select a file to upload.
                </p>
                </Dropzone>
                </div>
                </section>
        );
    }
}


class App extends Component {
    constructor(props) {
        super(props);
        this.unselectedColor = 'green';
        this.selectedColor = 'red';
        this.selected = [];
        this.infoText = [];
        const plotJSON = {
            data: [
                {
                    x: [],
                    y: [],
                    text: [],
                    type: 'scatter',
                    marker: {
                        color: [],
                        line: {
                            color: 'blue',
                            width: 10,
                        },
                        opacity: 0.6,
                        size: 9,
                    },
                }
            ],
            layout: {
                autosize: true,
                displaylogo: false,
                title: 'To get started, drag a JSON file into the box on left',
                yaxis: {
                    range: [0.0, 1.0]
                },
            },
            frames: [],
            config: {
                scrollZoom: true,
            },
        };

        this.state = {
            infoText: 'No node hovered',
            json: plotJSON,
            clearSelectionDisabled: true,
            exportSelectionDisabled: true,
        };

        this.handleDataChange = this.handleDataChange.bind(this);
        this.handleHover = this.handleHover.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.handlePlotUpdate = this.handlePlotUpdate.bind(this);
        this.handleClearSelection = this.handleClearSelection.bind(this);
        this.handleExportSelection = this.handleExportSelection.bind(this);
        this.handleSearchChange = this.handleSearchChange.bind(this);
    }
    
    handleHover(data) {
        this.setState({
            infoText: this.infoText[data.points[0].pointIndex],
        });
    }

    handleClick(e) {
        e.points.forEach(point => {
            let index = point.pointNumber;
            this.selected[index] = ! this.selected[index];
        });
        let selectedCount = 0;
        this.selected.forEach(selected => {
            if (selected){
                selectedCount++;
            }
        });
        let colors = [];
        for (var i = 0; i < this.state.json.data[0].x.length; i++){
            colors.push(
                this.selected[i] ? this.selectedColor : this.unselectedColor
            );
        }

        this.setState({
            clearSelectionDisabled: selectedCount === 0,
            exportSelectionDisabled: selectedCount === 0,
            json: {
                data: [{
                    x: this.state.json.data[0].x,
                    y: this.state.json.data[0].y,
                    text: this.state.json.data[0].text,
                    type: 'scatter',
                    mode: 'markers',
                    marker: {
                        color: colors,
                        opacity: 0.4,
                        size: 8,
                    },
                }],
                layout: {
                    autosize: true,
                    displaylogo: false,
                    title: this.sampleName,
                    yaxis: {
                        range: [0.0, 1.0]
                    },
                },
            }
        });
    }

    handleExportSelection(){
        let download = (data, filename, mime) => {
            var blob = new Blob([data], {type: mime || 'application/octet-stream'});
            if (typeof window.navigator.msSaveBlob !== 'undefined') {
                // IE workaround for "HTML7007: One or more blob URLs were 
                // revoked by closing the blob for which they were created. 
                // These URLs will no longer resolve as the data backing 
                // the URL has been freed."
                window.navigator.msSaveBlob(blob, filename);
            }
            else {
                var blobURL = window.URL.createObjectURL(blob);
                var tempLink = document.createElement('a');
                tempLink.style.display = 'none';
                tempLink.href = blobURL;
                tempLink.setAttribute('download', filename); 

                // Safari thinks _blank anchor are pop ups. We only want to set _blank
                // target if the browser does not support the HTML5 download attribute.
                // This allows you to download files in desktop safari if pop up blocking 
                // is enabled.
                if (typeof tempLink.download === 'undefined') {
                    tempLink.setAttribute('target', '_blank');
                }

                document.body.appendChild(tempLink);
                tempLink.click();
                document.body.removeChild(tempLink);
                window.URL.revokeObjectURL(blobURL);
            }
        };

        var queries = {};
        var data = [];
        for (var i = 0; i < this.state.json.data[0].x.length; i++){
            if (this.selected[i]){
                this.matchingQueries[i].forEach(name => {
                    queries[name] = true;
                });
            }
        }

        Object.keys(queries).forEach(name => {
            data.push('>' + name);
            data.push(this.queries[name]);
        });

        download(data.join('\n'), 'file.fasta', 'application/text');
    }

    handleClearSelection(){
        let colors = [];
        for (var i = 0; i < this.state.json.data[0].x.length; i++){
            colors.push(this.unselectedColor);
            this.selected[i] = false;
        }
        this.setState({
            clearSelectionDisabled: true,
            exportSelectionDisabled: true,
            json: {
                data: [{
                    x: this.state.json.data[0].x,
                    y: this.state.json.data[0].y,
                    text: this.state.json.data[0].text,
                    type: 'scatter',
                    mode: 'markers',
                    marker: {
                        color: colors,
                        opacity: 0.4,
                        size: 8,
                    },
                }],
                layout: {
                    autosize: true,
                    displaylogo: false,
                    title: this.sampleName,
                    xaxis: {
                        title: 'Match length',
                    },
                    yaxis: {
                        range: [0.0, 1.0],
                        title: 'Match identity fraction',
                    },
                },
            }
        });
    }

    handleSearchChange(e){
        console.log('search box change:', e.target.value);
    }

    handlePlotUpdate(figure) {
        this.setState(figure);
    }

    handleDataChange(data) {
        let colors = [];
        let markerLineColors = [];

        this.selected = [];
        this.sampleName = data.sampleName;
        for (var i = 0; i < data.x.length; i++){
            this.selected.push(false);
            colors.push(this.unselectedColor);
            markerLineColors.push(0);
        }
        this.queries = data.queries;
        this.matchingQueries = data.matchingQueries;
        this.infoText = data.infoText;
        this.setState({
            json: {
                data: [
                    {
                        x: data.x,
                        y: data.y,
                        text: data.hoverText,
                        type: 'scatter',
                        mode: 'markers',
                        marker: {
                            color: colors,
                            opacity: 0.4,
                            size: 9,
                            line: {
                                colorscale: [[0, this.unselectedColor], [1, 'rgb(255,0,0)']],
                                cmin: 0,
                                cmax: 1,
                                color: markerLineColors,
                                width: 3,
                            },
                        },
                    }
                ],
                layout: {
                    autosize: true,
                    displaylogo: false,
                    hovermode: 'closest',
                    title: 'Sample ' + data.sampleName,
                    xaxis: {
                        title: 'Match length',
                    },
                    yaxis: {
                        range: [0.0, 1.0],
                        title: 'Match identity fraction',
                    },
                },
            },
        });
    }

  render() {
    return (
            <div className="container-fluid">
            <Row style={{marginTop: "10px"}}>
            <Col md={2}>
            <FileDrop onDataChange={this.handleDataChange}/>
            <Panel>
            <Panel.Heading>
            <Panel.Title>Selection</Panel.Title>
            </Panel.Heading>
            <Panel.Body>
            <ButtonToolbar>
            <ClearSelectedButton
        disabled={this.state.clearSelectionDisabled}
        handleClearSelection={this.handleClearSelection}
            />
            <ExportSelectedButton
        disabled={this.state.exportSelectionDisabled}
        handleExportSelection={this.handleExportSelection}
            />
            </ButtonToolbar>
            </Panel.Body>
            </Panel>
            <SearchForm
        handleChange={this.handleSearchChange}
        />
            </Col>
            <Col md={10} style={{height: "600px"}}>
            <PlotlyApp
        data={this.state.json.data}
        layout={this.state.json.layout}
        frames={this.state.json.frames}
        config={this.state.json.config}
        onDataChange={this.handleDataChange}
        onClick={this.handleClick}
        onHover={this.handleHover}
        onUpdate={this.handlePlotUpdate}
            />
                  </Col>    
                </Row>    
                <Row>
            <Col md={12}>
            <Panel>
            <Panel.Heading>
            <Panel.Title>Hover info</Panel.Title>
            </Panel.Heading>
            <Panel.Body>
            <Infobox text={this.state.infoText}/>
            </Panel.Body>
            </Panel>
            </Col>
                </Row>    
            </div>
    );
  }
}

export default App;
