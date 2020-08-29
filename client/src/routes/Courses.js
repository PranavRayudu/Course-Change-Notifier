import React from 'react'
import {connect} from 'react-redux'
import {Button, Card, Form, Input, message, Space, Table, Tag} from 'antd'
import {green, grey, red, yellow} from '@ant-design/colors'
import {CaretRightOutlined, DeleteOutlined, PauseOutlined, PlusOutlined, ReloadOutlined,} from '@ant-design/icons'

import {fetchCourseData, postCourse, unpostCourses} from "../store/actions";

import AppStyles from '../app.module.scss'
import Pluralize from '../components/Pluralize'

const tagColors = {
    'open': green.primary,
    'open; reserved': green.primary,
    'reserved': yellow.primary,
    'waitlisted': yellow.primary,
    'waitlisted; reserved': yellow.primary,
    'closed': red.primary,
    'cancelled': grey.primary,
    'invalid': grey.primary,
}


class Courses extends React.Component {

    columns = [
        {
            title: 'ID',
            dataIndex: 'uid',
            render: (text, row) =>
                row.status === 'invalid' ? text :
                    <a href={`https://utdirect.utexas.edu/apps/registrar/course_schedule/${this.state.sid}/${text}/`}>{text}</a>,
            sorter: (a, b) => a.uid.localeCompare(b.uid),
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Abbr.',
            dataIndex: 'abbr',
            render: text => text ? text : '...',
        },
        {
            title: 'Title',
            dataIndex: 'title',
            render: text => text ? text : '...',
        },
        {
            title: 'Professor',
            dataIndex: 'prof',
            render: text => text ? text : '...',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            render: text => <Tag color={tagColors[text]}>{text}</Tag>,
        },
        {
            // title: 'Control',
            dataIndex: 'paused',
            render: (text, row) => text ?
                <Button type={"dashed"} icon={<CaretRightOutlined/>}
                        disabled={row.status === 'invalid'}
                        onClick={() => this.resumeCourse(row.uid)}/> :
                <Button type={"dashed"} icon={<PauseOutlined/>}
                        disabled={row.status === 'invalid'}
                        onClick={() => this.pauseCourse(row.uid)}/>,
        },
        {
            // title: 'Action',
            dataIndex: 'uid',
            render: (text, row) => row.status !== 'invalid' && <a
                href={`https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys=${this.props.sid}&s_af_unique=${text}`}
                target="_blank" rel="noopener noreferrer">Register</a>,
        },
    ];

    constructor(props) {
        super(props);

        this.state = {uid: '', data: [], selected: []}
        this.refreshData = this.refreshData.bind(this)
        this.handleSubmit = this.handleSubmit.bind(this)
    }

    componentDidMount() {
        this.refreshData()
        setInterval(this.refreshData, 1000 * 60 * 5) // every 5 min
    }


    handleSubmit(e) {
        // event.preventDefault()
        this.addCourse(this.state.uid)
        this.setState({uid: ''})
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
    }


    pauseCourse(uid) {
        this.props.dispatch(postCourse(uid, {pause: true}))
    }

    resumeCourse(uid) {
        this.props.dispatch(postCourse(uid, {pause: false}))
    }

    render() {
        // rowSelection object indicates the need for row selection
        const rowSelection = {
            onChange: (selectedRowKeys, selectedRows) => {
                this.setState({selected: selectedRows})
            },

            // getCheckboxProps: record => ({
            //     disabled: record.name === 'Disabled User',
            //     name: record.name,
            // }),
        };

        let tableHeader = <div className={AppStyles.heading}>
            <h3>Tracking {this.state.data.length}&nbsp;
                <Pluralize count={this.state.data.length}
                           word={"Course"}/></h3>

            <Space>
                <Form onFinish={this.handleSubmit} layout={"inline"}>
                    <Input.Group compact>
                        {/*<Form.Item name={"uid"}
                        rules={[{required: true}]}
                        style={{width: "50%"}}>*/}
                        <Input required
                               placeholder={"Course ID"}
                               pattern={"[0-9]{5}"}
                               value={this.state.uid}
                               onChange={e => this.setState({uid: e.target.value})}
                               style={{maxWidth: "100px"}}
                        />
                        {/*</Form.Item>*/}
                        {/*<Form.Item style={{width: "50%"}}>*/}
                        <Button type={"primary"}
                                htmlType={'submit'}>
                            <span className={AppStyles.hideSm}>Add</span>
                            <PlusOutlined/>
                        </Button>
                        {/*</Form.Item>*/}
                    </Input.Group>
                </Form>

                <Button type={"secondary"}
                        onClick={this.refreshData}>
                    <span className={AppStyles.hideSm}>Refresh</span><ReloadOutlined/>
                </Button>
                <Button type={"danger"}
                        onClick={() => this.deleteCourses(this.state.selected)}
                        disabled={this.state.selected.length === 0}>
                    <span className={AppStyles.hideSm}>Delete</span><DeleteOutlined/>
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
                    scroll={{x: 700}}
                    // bordered
                    // title={() => tableHeader}
                />
            </Space>
        </Card>;
    }
}

const mapStateToProps = state => {
    return {
        sid: state.sid,
        data: state.courses,
        loading: state.coursesLoading,
    }
}

export default connect(mapStateToProps)(Courses);


