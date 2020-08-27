import React from 'react'
import moment from 'moment'
import _ from 'lodash'
import {Row, Col, InputNumber, TimePicker, Space, Divider, Card, message, Button} from "antd"
import AppStyles from "../app.module.scss"

const {RangePicker} = TimePicker

function Control({label, control}) {

    return <Row>
        <Col flex={"0 1 150px"}>{label}</Col>
        <Col flex={"auto"}>{control}</Col>
    </Row>
}

const serialize = function (obj) {
    const str = [];
    for (let p in obj)
        if (obj.hasOwnProperty(p)) {
            str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
        }
    return str.join("&");
}

class Settings extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            interval: 0,
            timeRange: [null, null],

            fetchedInterval: 0,
            fetchedRange: [null, null]
        }

        this.setInterval = this.setInterval.bind(this)
        this.setRange = this.setRange.bind(this)
        this.sendConfig = this.sendConfig.bind(this)
        this.updateConfig = this.updateConfig.bind(this)
        this.send_debouce = _.debounce(this.updateConfig, 3000)
    }

    componentDidMount() {
        this.getConfig()
    }

    getConfig() {
        fetch('/api/v1/config').then((res) => {
            return res.json()
        }).then((data) => {
            let timeRange = [null, null]
            if (data.start && data.end)
                timeRange = [moment(data.start, 'HHmm'), moment(data.end, 'HHmm')]
            let interval = parseInt(data.interval)
            this.setState({
                interval: interval,
                timeRange: timeRange,
                fetchedInterval: interval,
                fetchedRange: timeRange,
            })
        }).catch(() => message.error('unable to query settings'))
    }

    updateConfig() {
        let send_dict = {}

        if (this.state.fetchedInterval !== this.state.interval) {
            send_dict['interval'] = this.state.interval
        }

        if (this.state.fetchedRange !== this.state.timeRange) {
            if (this.state.timeRange && this.state.timeRange[0] && this.state.timeRange[1]) {
                send_dict['start'] = this.state.timeRange[0].format('HHmm')
                send_dict['end'] = this.state.timeRange[1].format('HHmm')
            } else {
                send_dict['start'] = 'none'
                send_dict['end'] = 'none'
            }
        }

        this.sendConfig(serialize(send_dict))
    }

    sendConfig(data = '') {
        console.log('sending', data)
        fetch('/api/v1/config?' + data, {
            method: 'POST',
        }).then((res) => {
            if (!res.ok) throw new Error()
            message.success('updated settings successfully')
        }).catch(() => message.error('unable to update settings'))
            .finally(() => this.getConfig())
    }

    setInterval(val) {
        this.setState({interval: val})
        this.send_debouce()
    }

    setRange(range) {
        this.setState({timeRange: range ? range : [null, null]})
        this.send_debouce()
    }

    render() {
        return <Card bordered={false}>
            <div className={AppStyles.heading}>
                <Space direction={"vertical"} style={{width: "100%"}}>
                    <h3>Global Monitor Settings</h3>
                    <Control label={"Refresh Period"} control={
                        <span><InputNumber
                            min={1}
                            step={10}
                            value={this.state.interval}
                            onChange={this.setInterval}
                        />&nbsp;sec</span>}/>
                    {/*<Divider orientation={"left"} plain>Time Range</Divider>*/}
                    {/*<Control label={"Use time range"}*/}
                    {/*         control={<Switch checked={this.state.useRange} onChange={this.handleRange}/>}/>*/}
                    <Control label={"Range"} control={
                        <RangePicker
                            format={"HH:mm"}
                            value={this.state.timeRange}
                            minuteStep={15}
                            onChange={this.setRange}/>}/>
                    <Button type={"danger"} onClick={() => this.sendConfig()}>Reset</Button>
                </Space>
            </div>
        </Card>
    }
}

export default Settings


