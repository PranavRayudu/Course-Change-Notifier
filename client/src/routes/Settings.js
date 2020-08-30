import React from 'react'
import {connect} from "react-redux";
import {debounce} from 'lodash'
import {Button, Card, Col, InputNumber, message, Row, Space, TimePicker} from "antd"
import {postConfigData} from "../store/actions";
import AppStyles from "../app.module.scss"

const {RangePicker} = TimePicker

function Control({label, control}) {

    return <Row>
        <Col flex={"0 1 150px"}>{label}</Col>
        <Col flex={"auto"}>{control}</Col>
    </Row>
}

class Settings extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            interval: this.props.interval,
            timeRange: this.props.timeRange,
        }

        this.setInterval = this.setInterval.bind(this)
        this.setRange = this.setRange.bind(this)
        this.sendConfig = this.sendConfig.bind(this)
        this.updateConfig = this.updateConfig.bind(this)
        this.debouncedSend = debounce(this.updateConfig, 3000)
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps !== this.props) {
            this.setState({
                interval: this.props.interval,
                timeRange: this.props.timeRange
            })
        }
    }

    updateConfig() {
        const {interval, timeRange} = this.state
        this.sendConfig({interval: interval, timeRange: timeRange})
    }

    sendConfig(data) {
        this.debouncedSend.cancel() // in case reset was called
        this.props.dispatch(postConfigData(data,
            () => message.success('Updated settings'),
            () => message.error('Unable to update settings')
        ))
    }

    setInterval(val) {
        this.setState({interval: val})
        this.debouncedSend()
    }

    setRange(range) {
        this.setState({timeRange: range ? range : [null, null]})
        this.debouncedSend()
    }

    render() {
        return <Card bordered={false}>
            <div className={AppStyles.heading}>
                <Space direction={"vertical"} style={{width: "100%"}}>
                    <h3>Global Monitor Settings</h3>
                    <Control label={"Refresh Period"} control={
                        <span><InputNumber
                            min={1}
                            step={30}
                            value={this.state.interval}
                            onChange={this.setInterval}
                        />&nbsp;sec</span>}/>
                    <Control label={"Range"} control={
                        <RangePicker
                            format={"HH:mm"}
                            value={this.state.timeRange}
                            minuteStep={15}
                            clearText={'run course checking all the time'}
                            onChange={this.setRange}/>}/>
                    <Button type={"danger"} onClick={this.sendConfig}>Reset</Button>
                </Space>
            </div>
        </Card>
    }
}

const mapStateToProps = state => {
    return {
        interval: state.interval,
        timeRange: state.timeRange
    }
}

export default connect(mapStateToProps)(Settings);

