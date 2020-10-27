import React from 'react'
import {connect} from 'react-redux'
import moment from "moment";
import {Button, Card, Form, Input, message, Skeleton, Space, Switch, Table, Tag} from 'antd'
import {green, grey, red, yellow} from '@ant-design/colors'
import {
    CaretRightOutlined,
    DeleteOutlined,
    LinkOutlined,
    PauseOutlined,
    PlusOutlined,
    ReloadOutlined,
} from '@ant-design/icons'

import {fetchCourseData, postCourse, unpostCourses} from "../store/actions";

import AppStyles from '../app.module.scss'
import Pluralize from '../components/Pluralize'

const tagColors = {
    'open': green.primary,
    'open; reserved': green.primary,
    'reserved': yellow[6],
    'waitlisted': yellow[6],
    'waitlisted; reserved': yellow[6],
    'closed': red.primary,
    'cancelled': grey.primary,
    'invalid': grey.primary,
}

const registerColors = {
    'success': green.primary,
    'fail': red.primary
}

const within = (a, b) => {
    let now = moment()
    if (a && b) {
        if (a.isAfter(b)) { // reverse order, add to b
            if (now.isBefore(b)) a.subtract(1, 'days')
            else b.add(1, 'days')
        }
        return now.isBetween(a, b)
    }
    return true
}


class Courses extends React.Component {

    columns = [
        {
            title: 'ID',
            dataIndex: 'uid',
            render: (text, row) => <>
                {row.status === 'invalid' ? text :
                    <a href={`https://utdirect.utexas.edu/apps/registrar/course_schedule/${this.props.sid}/${text}/`}>{text}</a>}
                &nbsp; <a href={`https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys=${this.props.sid}&s_af_unique=${row.uid}`} style={{verticalAlign: "center"}}><LinkOutlined /></a>
                </>,
            sorter: (a, b) => a.uid.localeCompare(b.uid),
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Abbr.',
            dataIndex: 'abbr',
            render: text => text ? text : <Skeleton title={false} paragraph={{rows: 1}}/>,
        },
        {
            title: 'Title',
            dataIndex: 'title',
            render: text => text ? text : <Skeleton title={false} paragraph={{rows: 1}}/>,
        },
        {
            title: 'Professor',
            dataIndex: 'prof',
            render: text => text ? text : <Skeleton title={false} paragraph={{rows: 1}}/>,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            render: (text, row) => {
                return <>
                    <Tag color={tagColors[text]}>{text}</Tag>
                    {row.register && row.register !== 'register' &&
                    <Tag color={registerColors[row.register]}>registration {row.register}</Tag>}
                </>
            },
        },
        {
            title: 'Register',
            dataIndex: 'register',
            render: (text, row) => {
                let disabled = row.status === 'invalid'// || !this.state.running
                return <Switch disabled={disabled}
                           checked={text}
                           onChange={() => this.toggleCourseRegister(row.uid)}/>
            }
        },
        {
            dataIndex: 'paused',
            render: (text, row) => {
                let disabled = row.status === 'invalid'// || !this.state.running
                return text ?
                    <Button type={"dashed"} icon={<CaretRightOutlined/>}
                            disabled={disabled}
                            onClick={() => this.resumeCourse(row.uid)}/> :
                    <Button type={"dashed"} icon={<PauseOutlined/>}
                            disabled={disabled}
                            onClick={() => this.pauseCourse(row.uid)}/>
            },
        },
    ];

    constructor(props) {
        super(props);

        this.state = {uid: '', running: false, selected: []}
        this.refreshData = this.refreshData.bind(this)
        this.handleSubmit = this.handleSubmit.bind(this)
    }

    componentDidMount() {
        this.refreshData()
        setInterval(this.refreshData, 1000 * 60 * 5) // every 5 min

        this.updateRunning()
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps !== this.props) {
            this.updateRunning()
        }
    }

    handleSubmit(e) {
        // event.preventDefault()
        this.addCourse(this.state.uid)
        this.setState({uid: ''})
    }

    updateRunning() {
        this.setState({running: within(...Object.values(this.props.timeRange))})
    }

    refreshData() {
        this.props.dispatch(fetchCourseData(
            null,
            () => message.error('Unable to load course data')
        ))
    }

    addCourse(uid) {
        this.props.dispatch(postCourse(uid), null,
            () => message.success('Successfully added course'),
            () => message.error('Error when adding course'))
    }

    deleteCourses(courses) {
        this.props.dispatch(unpostCourses(courses,
            () => message.success('Successfully deleted courses'),
            () => message.error('Error deleting courses')
        ))
        this.setState({selected: []})
    }

    pauseCourse(uid) {
        this.props.dispatch(postCourse(uid, {pause: true}))
    }

    resumeCourse(uid) {
        this.props.dispatch(postCourse(uid, {pause: false}))
    }

    toggleCourseRegister(uid) {
        let course = this.props.data.find(c => c.uid === uid)
        this.props.dispatch(postCourse(uid, {register: !course.register}))
    }

    render() {
        const rowSelection = {
            onChange: (selectedRowKeys, selectedRows) => {
                this.setState({selected: selectedRows})
            },
        };

        let tableHeader = <div className={AppStyles.heading}>
            <h3>Tracking&nbsp;{this.props.data.length}&nbsp;
                <Pluralize count={this.props.data.length} word={"Course"}/>&nbsp;&nbsp;
                {this.state.running ?
                    <Tag color={"success"} style={{marginBottom: 3}}>Running</Tag> :
                    <Tag color={"warning"} style={{marginBottom: 3}}>Not Running</Tag>}
            </h3>

            <Space>
                <Form onFinish={this.handleSubmit} layout={"inline"}>
                    <Input.Group compact>
                        <Input required
                               placeholder={"Course ID"}
                               pattern={"[0-9]{5}"}
                               value={this.state.uid}
                               onChange={e => this.setState({uid: e.target.value})}
                               style={{maxWidth: "100px"}}/>
                        <Button type={"primary"}
                                htmlType={'submit'}
                                icon={<PlusOutlined/>}>
                            <span className={AppStyles.hideSm}>Add</span>
                        </Button>
                    </Input.Group>
                </Form>

                <Button type={"secondary"}
                        onClick={this.refreshData}
                        loading={this.props.loading}
                        icon={<ReloadOutlined/>}>
                    <span className={AppStyles.hideSm}>Refresh</span>
                </Button>
                <Button type={"danger"}
                        onClick={() => this.deleteCourses(this.state.selected)}
                        disabled={this.state.selected.length === 0}
                        icon={<DeleteOutlined/>}>
                    <span className={AppStyles.hideSm}>Delete</span>
                </Button>
            </Space>
        </div>

        return <Card bordered={false}>
            <Space direction={"vertical"} style={{width: "100%"}}>
                {tableHeader}
                <Table
                    rowSelection={{
                        type: "checkbox",
                        ...rowSelection
                    }}
                    columns={this.columns}
                    dataSource={this.props.data}
                    loading={this.props.loading}
                    pagination={false}
                    scroll={{x: 700}}/>
            </Space>
        </Card>;
    }
}

const mapStateToProps = state => {
    return {
        sid: state.sid,
        data: state.courses,
        loading: state.coursesLoading,
        timeRange: state.timeRange
    }
}

export default connect(mapStateToProps)(Courses);


